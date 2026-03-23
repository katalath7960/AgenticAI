#!/usr/bin/env bash
# =============================================================================
# deployment.sh — Feedback Intelligence System
# Azure Container Instances (cheapest option: pay-per-second, no idle cost)
#
# USAGE:
#   ./deployment.sh deploy    — Create all Azure resources and deploy
#   ./deployment.sh start     — Start a stopped container (resume billing)
#   ./deployment.sh stop      — Stop container to pause billing
#   ./deployment.sh status    — Show container status and public URL
#   ./deployment.sh logs      — Tail live container logs
#   ./deployment.sh update    — Rebuild image and redeploy in-place
#   ./deployment.sh open      — Open the app URL in the browser
#   ./deployment.sh destroy   — Delete ALL Azure resources (irreversible)
#   ./deployment.sh help      — Show this help
#
# ESTIMATED COST (Azure Container Instances):
#   ACR Basic         : ~$5 /month (image registry)
#   ACI 1vCPU/1.5GB   : ~$0.0000135/sec ≈ $0.05/hr — ZERO when stopped
#   Storage (10 GB)   : ~$1 /month (ChromaDB + data + docs)
#   ─────────────────────────────────────────────────────
#   Running 8 hrs/day : ~$18/month total
#   Stopped (idle)    : ~$6/month total   ← just registry + storage
#
# PRE-REQUISITES:
#   az login
#   Docker Desktop running
#   .env file with OPENAI_API_KEY set
# =============================================================================
set -euo pipefail

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; exit 1; }
step()    { echo -e "\n${BOLD}━━━ $* ━━━${RESET}"; }

# ── Configuration — edit these before first deploy ───────────────────────────
RESOURCE_GROUP="feedback-intelligence-rg"
LOCATION="eastus"                          # az account list-locations -o table
ACR_NAME="feedbackintelacr"                # globally unique, lowercase, alphanumeric
STORAGE_ACCOUNT="feedbackintelsa"          # globally unique, 3-24 chars, lowercase
CONTAINER_NAME="feedback-intelligence"
IMAGE_NAME="feedback-intelligence"
IMAGE_TAG="latest"
CPU="1"                                    # vCPUs  (0.5–4)
MEMORY="1.5"                               # GB RAM (0.5–16)
PORT="8501"                                # Streamlit internal port
DNS_LABEL="feedback-intel"                 # must be globally unique → public URL
# ─────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

# ── Load .env ─────────────────────────────────────────────────────────────────
load_env() {
    if [[ ! -f "$ENV_FILE" ]]; then
        error ".env file not found at $ENV_FILE\nRun: cp .env.example .env  then fill in OPENAI_API_KEY"
    fi
    # Export only non-comment, non-empty lines
    set -o allexport
    # shellcheck disable=SC1090
    source <(grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$')
    set +o allexport

    if [[ -z "${OPENAI_API_KEY:-}" ]]; then
        error "OPENAI_API_KEY is empty in .env — set it before deploying"
    fi
    success "Loaded .env (OPENAI_API_KEY=sk-...${OPENAI_API_KEY: -4})"
}

# ── Guard: require az CLI ──────────────────────────────────────────────────────
require_az() {
    if ! command -v az &>/dev/null; then
        error "Azure CLI not found. Install from https://aka.ms/installazurecliwindows"
    fi
    if ! az account show &>/dev/null; then
        error "Not logged in to Azure. Run: az login"
    fi
}

# ── Guard: require Docker ─────────────────────────────────────────────────────
require_docker() {
    if ! command -v docker &>/dev/null; then
        error "Docker not found or not running."
    fi
}

# ── Derive full image reference ───────────────────────────────────────────────
acr_login_server() {
    az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" \
        --query loginServer -o tsv 2>/dev/null
}

full_image_ref() {
    echo "$(acr_login_server)/${IMAGE_NAME}:${IMAGE_TAG}"
}

# =============================================================================
# COMMAND: deploy
# =============================================================================
cmd_deploy() {
    load_env
    require_az
    require_docker

    step "1 / 7  Resource Group"
    if az group show --name "$RESOURCE_GROUP" &>/dev/null; then
        warn "Resource group '$RESOURCE_GROUP' already exists — skipping"
    else
        az group create --name "$RESOURCE_GROUP" --location "$LOCATION" -o none
        success "Created resource group '$RESOURCE_GROUP' in $LOCATION"
    fi

    step "2 / 7  Azure Container Registry (Basic — cheapest)"
    if az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
        warn "ACR '$ACR_NAME' already exists — skipping"
    else
        az acr create \
            --resource-group "$RESOURCE_GROUP" \
            --name "$ACR_NAME" \
            --sku Basic \
            --admin-enabled true \
            -o none
        success "Created ACR '$ACR_NAME' (Basic tier)"
    fi

    step "3 / 7  Storage Account + File Shares (for persistent volumes)"
    if az storage account show --name "$STORAGE_ACCOUNT" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
        warn "Storage account '$STORAGE_ACCOUNT' already exists — skipping"
    else
        az storage account create \
            --name "$STORAGE_ACCOUNT" \
            --resource-group "$RESOURCE_GROUP" \
            --location "$LOCATION" \
            --sku Standard_LRS \
            --kind StorageV2 \
            -o none
        success "Created storage account '$STORAGE_ACCOUNT'"
    fi

    STORAGE_KEY=$(az storage account keys list \
        --resource-group "$RESOURCE_GROUP" \
        --account-name "$STORAGE_ACCOUNT" \
        --query "[0].value" -o tsv)

    for SHARE in feedback-data feedback-docs; do
        if az storage share show --name "$SHARE" --account-name "$STORAGE_ACCOUNT" \
            --account-key "$STORAGE_KEY" &>/dev/null 2>&1; then
            warn "File share '$SHARE' already exists — skipping"
        else
            az storage share create \
                --name "$SHARE" \
                --account-name "$STORAGE_ACCOUNT" \
                --account-key "$STORAGE_KEY" \
                --quota 10 \
                -o none
            success "Created file share '$SHARE' (10 GB)"
        fi
    done

    step "4 / 7  Build Docker image"
    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" "$SCRIPT_DIR"
    success "Built image ${IMAGE_NAME}:${IMAGE_TAG}"

    step "5 / 7  Push image to ACR"
    az acr login --name "$ACR_NAME"
    LOCAL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"
    REMOTE_IMAGE="$(full_image_ref)"
    docker tag "$LOCAL_IMAGE" "$REMOTE_IMAGE"
    docker push "$REMOTE_IMAGE"
    success "Pushed image → $REMOTE_IMAGE"

    step "6 / 7  Deploy Azure Container Instance"
    ACR_SERVER=$(acr_login_server)
    ACR_USER=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
    ACR_PASS=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

    # Delete existing container if present (update scenario)
    if az container show --name "$CONTAINER_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
        warn "Container '$CONTAINER_NAME' already exists — deleting for fresh deploy"
        az container delete --name "$CONTAINER_NAME" --resource-group "$RESOURCE_GROUP" --yes -o none
        info "Waiting for deletion to complete..."
        sleep 15
    fi

    az container create \
        --resource-group "$RESOURCE_GROUP" \
        --name "$CONTAINER_NAME" \
        --image "$(full_image_ref)" \
        --registry-login-server "$ACR_SERVER" \
        --registry-username "$ACR_USER" \
        --registry-password "$ACR_PASS" \
        --cpu "$CPU" \
        --memory "$MEMORY" \
        --ports "$PORT" \
        --protocol TCP \
        --dns-name-label "$DNS_LABEL" \
        --os-type Linux \
        --restart-policy Always \
        --environment-variables \
            OPENAI_MODEL="${OPENAI_MODEL:-gpt-4o}" \
            PYTHONUNBUFFERED="1" \
            PYTHONDONTWRITEBYTECODE="1" \
            DATA_DIR="/app/data/input" \
            OUTPUT_DIR="/app/data/output" \
            CHROMA_PATH="/app/data/chroma" \
            TECH_DOCS_DIR="/app/docs/product" \
            CLASSIFICATION_THRESHOLD="${CLASSIFICATION_THRESHOLD:-0.7}" \
            DUPLICATE_SIMILARITY_THRESHOLD="${DUPLICATE_SIMILARITY_THRESHOLD:-0.85}" \
            CLASSIFIER_BATCH_SIZE="${CLASSIFIER_BATCH_SIZE:-10}" \
        --secure-environment-variables \
            OPENAI_API_KEY="$OPENAI_API_KEY" \
        --azure-file-volume-account-name "$STORAGE_ACCOUNT" \
        --azure-file-volume-account-key "$STORAGE_KEY" \
        --azure-file-volume-share-name "feedback-data" \
        --azure-file-volume-mount-path "/app/data" \
        -o none

    success "Container deployed!"

    step "7 / 7  Deployment complete"
    cmd_status
    echo ""
    info "TIP: Stop the container when not in use to avoid charges:"
    info "     ./deployment.sh stop"
}

# =============================================================================
# COMMAND: update  (rebuild + redeploy without recreating infrastructure)
# =============================================================================
cmd_update() {
    load_env
    require_az
    require_docker

    step "Rebuilding and redeploying image"

    info "Building new image..."
    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" "$SCRIPT_DIR"

    info "Logging in to ACR..."
    az acr login --name "$ACR_NAME"

    info "Pushing image to ACR..."
    REMOTE_IMAGE="$(full_image_ref)"
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "$REMOTE_IMAGE"
    docker push "$REMOTE_IMAGE"
    success "Pushed $REMOTE_IMAGE"

    info "Restarting container with new image..."
    az container restart \
        --name "$CONTAINER_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        -o none

    success "Container restarted with updated image"
    cmd_status
}

# =============================================================================
# COMMAND: start
# =============================================================================
cmd_start() {
    require_az
    step "Starting container '$CONTAINER_NAME'"
    az container start \
        --name "$CONTAINER_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        -o none
    success "Container started"
    cmd_status
}

# =============================================================================
# COMMAND: stop  (pauses billing)
# =============================================================================
cmd_stop() {
    require_az
    step "Stopping container '$CONTAINER_NAME' (billing paused)"
    az container stop \
        --name "$CONTAINER_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        -o none
    success "Container stopped — compute billing paused"
    info "Storage (~\$1/mo) and ACR (~\$5/mo) charges continue"
    info "Restart with: ./deployment.sh start"
}

# =============================================================================
# COMMAND: status
# =============================================================================
cmd_status() {
    require_az

    if ! az container show --name "$CONTAINER_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
        warn "Container '$CONTAINER_NAME' does not exist. Run: ./deployment.sh deploy"
        return
    fi

    STATE=$(az container show \
        --name "$CONTAINER_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "instanceView.state" -o tsv)

    FQDN=$(az container show \
        --name "$CONTAINER_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "ipAddress.fqdn" -o tsv)

    IP=$(az container show \
        --name "$CONTAINER_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "ipAddress.ip" -o tsv)

    echo ""
    echo -e "  ${BOLD}Container:${RESET}  $CONTAINER_NAME"
    echo -e "  ${BOLD}State:${RESET}      $STATE"
    echo -e "  ${BOLD}IP:${RESET}         $IP"
    if [[ -n "$FQDN" ]]; then
        echo -e "  ${BOLD}URL:${RESET}        ${GREEN}http://${FQDN}:${PORT}${RESET}"
    fi
    echo ""
}

# =============================================================================
# COMMAND: logs
# =============================================================================
cmd_logs() {
    require_az
    step "Live logs for '$CONTAINER_NAME' (Ctrl+C to stop)"
    az container logs \
        --name "$CONTAINER_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --follow
}

# =============================================================================
# COMMAND: open
# =============================================================================
cmd_open() {
    require_az

    FQDN=$(az container show \
        --name "$CONTAINER_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "ipAddress.fqdn" -o tsv 2>/dev/null)

    if [[ -z "$FQDN" ]]; then
        error "Cannot find FQDN — is the container deployed and running?"
    fi

    URL="http://${FQDN}:${PORT}"
    info "Opening $URL"

    # Cross-platform open
    if command -v xdg-open &>/dev/null; then
        xdg-open "$URL"
    elif command -v open &>/dev/null; then
        open "$URL"
    elif command -v start &>/dev/null; then
        start "$URL"
    else
        info "Open manually: $URL"
    fi
}

# =============================================================================
# COMMAND: destroy  (deletes everything — irreversible)
# =============================================================================
cmd_destroy() {
    require_az

    echo ""
    echo -e "${RED}${BOLD}WARNING: This will permanently delete:${RESET}"
    echo -e "  • Resource group : $RESOURCE_GROUP"
    echo -e "  • All resources inside it (ACR, ACI, Storage)"
    echo -e "  • All stored data (ChromaDB, output CSVs, uploaded docs)"
    echo ""
    read -r -p "Type 'yes' to confirm destruction: " CONFIRM
    if [[ "$CONFIRM" != "yes" ]]; then
        info "Aborted."
        exit 0
    fi

    step "Deleting resource group '$RESOURCE_GROUP' (this takes ~2 min)"
    az group delete --name "$RESOURCE_GROUP" --yes --no-wait -o none
    success "Deletion initiated (running in background)"
    info "Monitor: az group show --name $RESOURCE_GROUP --query properties.provisioningState -o tsv"
}

# =============================================================================
# COMMAND: help
# =============================================================================
cmd_help() {
    echo ""
    echo -e "${BOLD}Feedback Intelligence System — Azure Deployment${RESET}"
    echo ""
    echo -e "  ${CYAN}./deployment.sh deploy${RESET}   Create all Azure resources and deploy container"
    echo -e "  ${CYAN}./deployment.sh start${RESET}    Start a stopped container"
    echo -e "  ${CYAN}./deployment.sh stop${RESET}     Stop container (pauses compute billing)"
    echo -e "  ${CYAN}./deployment.sh status${RESET}   Show container state and public URL"
    echo -e "  ${CYAN}./deployment.sh logs${RESET}     Tail live container logs"
    echo -e "  ${CYAN}./deployment.sh update${RESET}   Rebuild image and redeploy"
    echo -e "  ${CYAN}./deployment.sh open${RESET}     Open the app in the browser"
    echo -e "  ${CYAN}./deployment.sh destroy${RESET}  Delete ALL Azure resources"
    echo ""
    echo -e "${BOLD}Config (edit top of this file):${RESET}"
    echo -e "  RESOURCE_GROUP  = $RESOURCE_GROUP"
    echo -e "  LOCATION        = $LOCATION"
    echo -e "  ACR_NAME        = $ACR_NAME"
    echo -e "  STORAGE_ACCOUNT = $STORAGE_ACCOUNT"
    echo -e "  CONTAINER_NAME  = $CONTAINER_NAME"
    echo -e "  DNS_LABEL       = $DNS_LABEL"
    echo -e "  CPU / MEMORY    = ${CPU} vCPU / ${MEMORY} GB"
    echo ""
    echo -e "${BOLD}Estimated cost:${RESET}"
    echo -e "  Running  (8 hr/day) : ~\$18/month"
    echo -e "  Stopped  (idle)     : ~\$6/month  (ACR + Storage only)"
    echo ""
    echo -e "${BOLD}Pre-requisites:${RESET}"
    echo -e "  az login                        # authenticate to Azure"
    echo -e "  cp .env.example .env            # set OPENAI_API_KEY"
    echo -e "  Docker Desktop running"
    echo ""
}

# =============================================================================
# Entrypoint
# =============================================================================
COMMAND="${1:-help}"

case "$COMMAND" in
    deploy)  cmd_deploy  ;;
    start)   cmd_start   ;;
    stop)    cmd_stop    ;;
    status)  cmd_status  ;;
    logs)    cmd_logs    ;;
    update)  cmd_update  ;;
    open)    cmd_open    ;;
    destroy) cmd_destroy ;;
    help|--help|-h) cmd_help ;;
    *)
        error "Unknown command: $COMMAND\nRun: ./deployment.sh help"
        ;;
esac
