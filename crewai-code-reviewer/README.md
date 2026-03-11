# CrewAI Code Review Agent

Automated code review for **React** + **.NET Core Web API** projects.  
Five AI agents analyze your code and produce a Markdown report covering quality, security, performance, and best practices.

---

## What's Inside

```
crewai-code-reviewer/
├── main.py                  ← Review a local project folder
├── review_pr.py             ← Review a GitHub pull request
├── review_ado_pr.py         ← Review an Azure DevOps pull request
├── requirements.txt         ← Python dependencies
├── .env.example             ← Template for your API keys
│
├── agents/                  ← 5 specialized reviewer agents
│   ├── frontend_reviewer.py    React / TS / JS
│   ├── backend_reviewer.py     .NET Core / C#
│   ├── security_reviewer.py    OWASP / AppSec
│   ├── performance_reviewer.py Full-stack perf
│   └── quality_auditor.py      SOLID / clean code
│
├── tasks/                   ← Task definitions & prompts
│   └── review_tasks.py
│
├── tools/                   ← File scanning, GitHub, Azure DevOps
│   ├── file_scanner.py
│   ├── code_analyzer.py
│   ├── github_integration.py
│   └── azure_devops_integration.py
│
├── utils/
│   └── report_generator.py
│
├── config/
│   └── settings.py
│
└── sample_project/          ← Test files with intentional bugs
    ├── frontend/src/components/
    │   ├── UserDashboard.jsx
    │   └── LoginForm.jsx
    └── backend/
        ├── Controllers/UsersController.cs
        └── Services/UserService.cs
```

---

## Setup (5 minutes)

### Step 1 — Unzip

Unzip the downloaded file anywhere on your machine:

```bash
unzip crewai-code-reviewer.zip
cd crewai-code-reviewer
```

### Step 2 — Create a Python virtual environment

Requires Python 3.10 or newer.

```bash
python -m venv .venv

# Activate it:
# macOS / Linux:
source .venv/bin/activate

# Windows PowerShell:
.venv\Scripts\Activate.ps1

# Windows cmd:
.venv\Scripts\activate.bat
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Add your API key

```bash
cp .env.example .env
```

Open `.env` in any text editor and fill in **one** LLM provider key:

```dotenv
# OPTION A — OpenAI (recommended, works out of the box)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
OPENAI_MODEL_NAME=gpt-4o

# OPTION B — Anthropic
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# OPTION C — Free local model via Ollama (no API key needed)
# OPENAI_API_BASE=http://localhost:11434/v1
# OPENAI_API_KEY=ollama
# OPENAI_MODEL_NAME=llama3
```

That's it — you're ready to run.

---

## Usage

### A) Review a local project folder

Point it at any folder that contains `.jsx` / `.tsx` / `.ts` / `.js` / `.cs` files:

```bash
python main.py --path /path/to/your/project
```

Try the included sample project first to see it in action:

```bash
python main.py --path ./sample_project
```

More options:

```bash
# Only run specific review areas
python main.py --path ./my-app --focus frontend security

# Save report to a specific file
python main.py --path ./my-app --output my-review.md

# See full agent reasoning
python main.py --path ./my-app --verbose

# Limit number of files scanned
python main.py --path ./my-app --max-files 20
```

---

### B) Review an Azure DevOps pull request

#### One-time setup

1. Go to `https://dev.azure.com/{your-org}/_usersSettings/tokens`
2. Click **New Token**
3. Give it a name (e.g. "Code Review Bot")
4. Set scope: **Code → Read & Write**
5. Copy the token

Add these three lines to your `.env` file:

```dotenv
AZURE_DEVOPS_ORG=your-organisation-name
AZURE_DEVOPS_PROJECT=your-project-name
AZURE_DEVOPS_PAT=the-token-you-just-copied
```

#### Run

```bash
# Review the latest active PR in a repo
python review_ado_pr.py --repo MyWebApp

# Review a specific PR by number
python review_ado_pr.py --repo MyWebApp --pr 1234

# Only review PRs targeting a specific branch
python review_ado_pr.py --repo MyWebApp --target-branch main

# Review AND post the report as a comment on the PR
python review_ado_pr.py --repo MyWebApp --post-comment

# Override org/project without changing .env
python review_ado_pr.py --repo MyWebApp --org contoso --project WebTeam

# Combine flags
python review_ado_pr.py --repo MyWebApp --target-branch develop --post-comment --verbose
```

---

### C) Review a GitHub pull request

Add to your `.env`:

```dotenv
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

```bash
# Review a PR
python review_pr.py --repo owner/repo --pr 42

# Review and post the report as a PR comment
python review_pr.py --repo owner/repo --pr 42 --post-comment
```

---

## Output

Every run produces a Markdown file (saved in the current directory) that includes:

- Executive summary with an overall quality score (0–100)
- Score breakdown table (frontend, backend, security, performance, quality)
- Every issue found — with file name, severity, description, and fix
- Prioritised refactoring roadmap (immediate → short-term → long-term)

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'crewai'` | Make sure your virtual environment is activated and you ran `pip install -r requirements.txt` |
| `openai.AuthenticationError` | Check that `OPENAI_API_KEY` in `.env` is correct and has credits |
| `Azure DevOps API error 401` | Your PAT is wrong or expired — generate a new one |
| `Azure DevOps API error 403` | Your PAT doesn't have **Code Read & Write** scope |
| `No active pull requests found` | There's no open/active PR in that repo — try `--pr <number>` to target a specific one |
| Review is slow | Each agent makes LLM calls sequentially — a full 5-agent review of 20 files takes ~3-5 minutes with GPT-4o |

---

## How It Works

1. **Scanner** walks your project and finds all `.jsx`, `.tsx`, `.ts`, `.js`, `.cs` files
2. **Loader** reads file contents and builds a context block (respects size limits)
3. **5 agents** run in sequence, each producing a structured findings report:
   - Frontend Reviewer → React patterns, hooks, a11y, anti-patterns
   - Backend Reviewer → .NET controllers, DI, async, REST design
   - Security Reviewer → OWASP Top-10, XSS, injection, auth, secrets
   - Performance Reviewer → re-renders, N+1, caching, memory
   - Quality Auditor → SOLID, clean code, duplication, naming
4. **Aggregator** combines all findings into a single scored report
5. **Report** is saved as Markdown (and optionally posted to your PR)

## License

MIT
