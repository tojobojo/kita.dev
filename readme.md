# ⚡ Kita.dev

> **Open Source Autonomous Coding Agent**  
> _Maintains your codebase, writes tests, and fixes bugs automatically._

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Actions](https://github.com/user/kita.dev/actions/workflows/ci.yml/badge.svg)](https://github.com/user/kita.dev/actions)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](Dockerfile)
[![Built with FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Frontend React](https://img.shields.io/badge/React-19-61dafb.svg?style=flat&logo=react&logoColor=black)](https://react.dev)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/new?template-paths=.&envs=OPENAI_API_KEY,GITHUB_APP_ID,GITHUB_PRIVATE_KEY,GITHUB_WEBHOOK_SECRET)
[![Deploy to DigitalOcean](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/user/kita.dev/tree/main)

---

## What is Kita.dev?

Kita.dev is a fully autonomous coding agent that integrates directly with your GitHub repository. Unlike copilot tools that suggest code while you type, Kita runs in the background to handle complete tasks:

- 🧪 **Add missing tests** to your codebase
- 🐛 **Fix bugs** reported in issues
- 🧹 **Refactor legacy code** and fix lint errors
- 🔒 **Verify security** logic

It uses a secure, sandboxed environment (Docker) to execute code, run tests, and verify its own work before opening a Pull Request.

## Features

- **Autonomous Execution Loop**: Plans, executes, tests, and reflects on failures.
- **Sandboxed Environment**: Runs all untrusted code in an isolated Docker container with network restrictions.
- **GitHub Native**: Works via webhook—just comment `@kita-bot` on any issue.
- **Safety First**: Budget limits (tokens/cost), command allowlisting, and secret redaction.
- **Production Ready**: One-click deploy, structured logging, and Prometheus metrics.

## Quick Start

### 1. One-Click Deploy

Use the Railway button above to deploy your own instance. expected to cost ~$5/month for hosting + OpenAI API usage.

### 2. Local Development

Prerequisites: Python 3.11+, Node.js 20+, Docker.

```bash
# Clone the repo
git clone https://github.com/user/kita.dev.git
cd kita.dev

# Setup Backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Setup Frontend
cd ui
npm install
npm run dev
# (Keep this running)

# Run Backend (in new terminal)
docker-compose up -d sandbox  # Start sandbox container
uvicorn api.app:app --reload --port 8080
```

Visit the dashboard at `http://localhost:5173`.

## Documentation

- [Deployment Guide](deploy/README.md)
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Prometheus Metrics](api/middleware/metrics.py)

## Contributing

We love contributions! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

## License

This project is licensed under the [MIT License](LICENSE).
