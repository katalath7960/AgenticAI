# Deployment Notes

## Local / on-site (single host)

Simplest path — the event laptop or a staff laptop on the venue LAN:

```bash
cp .env.example .env        # edit SMTP creds
docker compose -f docker/docker-compose.yml up --build
```

Services:
- API:        http://<host>:8000  (OpenAPI at /docs)
- Frontend:   http://<host>:5173  (scanner UI for staff devices)
- Streamlit:  http://<host>:8501  (admin dashboard)

Staff phones/tablets on the same WiFi open `http://<laptop-ip>:5173`. Camera access requires HTTPS on most browsers — either deploy behind a reverse proxy with a cert (mkcert for LAN, Caddy for auto-TLS on a domain) or allow the browser's camera permission for the LAN address.

## Azure Container Apps

1. Build and push three images to ACR:
   ```bash
   az acr build -r <registry> -t wfh-api:latest      -f docker/Dockerfile.api .
   az acr build -r <registry> -t wfh-frontend:latest -f docker/Dockerfile.frontend .
   az acr build -r <registry> -t wfh-streamlit:latest -f docker/Dockerfile.streamlit .
   ```
2. Create an Azure Container Apps environment.
3. Deploy each image as its own Container App:
   - `wfh-api` — ingress external, port 8000, secrets for SMTP
   - `wfh-frontend` — ingress external, port 80, build-arg `VITE_API_BASE_URL=<api public URL>`
   - `wfh-streamlit` — ingress external, port 8501
4. Mount an Azure Files share at `/app/data` for the api + streamlit apps (shared DB + barcode PNGs).

## Render / Fly.io

Any of the three Dockerfiles deploy as-is. Set a persistent volume for `/app/data`. Frontend only needs a static-site deploy from `dist/` — the nginx stage is optional on platforms that already serve statics.

## Production notes

- **Database**: swap SQLite for Postgres by setting `DATABASE_URL=postgresql+psycopg://user:pw@host/db`. No code changes needed — `alembic upgrade head` will provision the schema. SQLite is fine for the ~1,000-row event, but a single file on a shared volume is a single point of failure.
- **SMTP**: Gmail has a ~500-msg/day soft limit on consumer accounts. For 1,000 attendees, switch to a transactional provider (SendGrid free tier, Mailgun sandbox) or split sends across two days. Use a dedicated service account with an App Password — never your primary account password.
- **Secrets**: `.env` should never be committed. In containerized environments inject via the platform's secret store (Azure Key Vault reference, Render env group, Fly secrets).
- **CORS**: the API currently whitelists `localhost:5173 / :8501 / :3000`. Add the production frontend origin to `cors_origins` in `api/main.py` before deploying.
- **Scaling**: the API is stateless apart from the DB; horizontal scaling works once the DB is Postgres. The agent background task uses an in-process dict for run status — if you need HA, persist runs to the DB instead.
- **TLS**: camera-based scanning in browsers requires HTTPS (or `localhost`). Terminate TLS at Azure Container Apps ingress, Render's built-in proxy, or a Caddy/Traefik sidecar.
