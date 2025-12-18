# OpsLens — Multimodal On-Call Copilot

<div align="center">

**An AI-powered incident response system that transforms chaos into clarity**

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.0-black.svg)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## 🎯 Overview

OpsLens is an end-to-end incident-response copilot that transforms messy, real-world signals (alerts, logs, metrics, traces, screenshots, runbooks, PRs) into actionable intelligence:

- **Live incident timeline** - "What changed, when, and likely why"
- **Ranked hypotheses** - AI-generated root cause analysis with supporting evidence
- **Actionable next steps** - Queries to run, owners to page, rollback plans
- **Postmortem drafts** - Automatic generation with root-cause candidates and follow-ups

### The Problem It Solves

On-call engineers waste precious time context-switching across tools (PagerDuty → Slack → Datadog/Grafana → GitHub → runbooks). OpsLens reduces MTTR (Mean Time To Resolution) by:

- **Connecting evidence across systems** - Automatically correlates alerts, deployments, and metrics
- **Multimodal understanding** - Uses Vision-Language Models (VLM) to analyze dashboard screenshots
- **Structured incident state** - Maintains a deterministic, trustworthy incident timeline
- **AI-powered insights** - Generates hypotheses and suggests actions based on historical patterns

## ✨ Features

### Core Functionality

- **🔗 Real-time Integrations**
  - GitHub - Fetches recent PR merges and deployment information
  - PagerDuty - Pulls active incidents and alerts
  - Extensible architecture for additional integrations (Slack, Datadog, Grafana, etc.)

- **🤖 AI-Powered Analysis**
  - **LLM Integration** (Llama 3.1) - Summarizes logs, generates hypotheses, drafts postmortems
  - **VLM Integration** (Qwen2.5-VL) - Analyzes dashboard screenshots and extracts insights
  - **RAG System** (BGE-M3) - Semantic search over runbooks and historical postmortems

- **📊 Incident Management**
  - Event-driven timeline generation
  - Deterministic incident state machine
  - Evidence correlation and ranking
  - Action tracking and completion

- **🎨 Modern UI**
  - War Room view with live timeline
  - Evidence viewer with screenshot understanding
  - Hypothesis ranking with confidence scores
  - Action queue with completion tracking

## 🏗️ Architecture

### Tech Stack

**Backend:**
- **FastAPI** - High-performance async API framework
- **PostgreSQL + pgvector** - Relational database with vector embeddings support
- **Celery + Redis** - Distributed task queue for async processing
- **Hugging Face Inference API** - LLM, VLM, and embedding models

**Frontend:**
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling

**Infrastructure:**
- **Docker Compose** - Containerized development environment
- **Postgres with pgvector extension** - Vector similarity search
- **Redis** - Task queue and caching

### System Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│   FastAPI    │────▶│  PostgreSQL │
│  (Next.js)  │     │   Backend    │     │  + pgvector │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ├────▶ Celery Workers
                            │         │
                            │         ├── GitHub Integration
                            │         ├── PagerDuty Integration
                            │         └── ML Processing
                            │
                            └────▶ Hugging Face API
                                   (LLM, VLM, Embeddings)
```

## 🚀 Quick Start

### Prerequisites

- Docker Desktop installed and running
- API keys for:
  - [Hugging Face](https://huggingface.co/settings/tokens) (free tier available)
  - [GitHub](https://github.com/settings/tokens) (Personal Access Token with `repo` scope)
  - [PagerDuty](https://support.pagerduty.com/docs/api-keys) (API key from your account)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/OpsLens.git
   cd OpsLens
   ```

2. **Set up environment variables:**
   ```bash
   cp secrets.env.example secrets.env
   # Edit secrets.env and add your API keys
   ```

3. **Start the application:**
   ```bash
   ./setup.sh
   ```
   
   Or manually:
   ```bash
   docker-compose up -d
   docker-compose exec backend python -m app.db.init_db
   docker-compose exec backend python -m app.data.generate_synthetic
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 📁 Project Structure

```
OpsLens/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # REST API endpoints
│   │   │   ├── incidents.py
│   │   │   ├── evidence.py
│   │   │   ├── hypotheses.py
│   │   │   ├── runbooks.py
│   │   │   └── integrations.py
│   │   ├── db/             # Database models and setup
│   │   │   ├── models.py
│   │   │   └── init_db.py
│   │   ├── integrations/   # External service integrations
│   │   │   ├── github.py
│   │   │   └── pagerduty.py
│   │   ├── services/        # Business logic
│   │   │   ├── ml_service.py
│   │   │   ├── rag_service.py
│   │   │   └── incident_service.py
│   │   ├── workers/         # Celery async tasks
│   │   │   ├── incident_worker.py
│   │   │   └── evidence_worker.py
│   │   ├── data/            # Data generation utilities
│   │   │   └── generate_synthetic.py
│   │   ├── config.py        # Configuration management
│   │   ├── main.py          # FastAPI application
│   │   └── celery_app.py   # Celery configuration
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                # Next.js frontend
│   ├── app/                # Next.js app directory
│   │   ├── page.tsx         # Incident list
│   │   ├── incidents/[id]/  # Incident detail page
│   │   └── layout.tsx
│   ├── lib/                 # Utilities
│   │   ├── api.ts          # API client
│   │   └── types.ts        # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml       # Docker orchestration
├── setup.sh                 # Setup script
├── secrets.env.example      # Environment template
└── README.md
```

## 🔧 Development

### Running Locally

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f [service_name]

# Restart a service
docker-compose restart [service_name]

# Stop all services
docker-compose down
```

### Testing Integrations

Test your GitHub and PagerDuty integrations:

```bash
# Test GitHub
curl http://localhost:8000/api/v1/integrations/test/github

# Test PagerDuty
curl http://localhost:8000/api/v1/integrations/test/pagerduty

# Test all
curl http://localhost:8000/api/v1/integrations/test/all
```

### Adding New Integrations

1. Create integration module in `backend/app/integrations/`
2. Add API endpoints in `backend/app/api/integrations.py`
3. Create Celery tasks for async processing
4. Update incident worker to use new integration

## 📖 Usage

### Creating an Incident

1. Navigate to http://localhost:3000
2. View existing incidents or create a new one via API
3. Click on an incident to view details

### Generating Timeline

1. Open an incident detail page
2. Click "Generate Timeline" button
3. System will:
   - Fetch recent GitHub PR merges (last 24 hours)
   - Fetch recent PagerDuty incidents
   - Correlate events chronologically
   - Display in timeline view

### Analyzing Screenshots

1. Go to the Evidence tab
2. Upload a dashboard screenshot
3. VLM will analyze and extract:
   - Error patterns
   - Metric anomalies
   - Important insights

### Generating Hypotheses

1. Click "Generate Hypotheses" on an incident
2. AI will analyze evidence and generate:
   - Root cause hypotheses
   - Confidence scores
   - Supporting evidence links

## 🧪 Testing

The project includes realistic synthetic data for testing:

```bash
docker-compose exec backend python -m app.data.generate_synthetic
```

This generates 5 realistic incident scenarios with:
- Coherent timelines
- Relevant evidence
- Realistic hypotheses
- Actionable next steps

## 🔐 Security

- API keys stored in `secrets.env` (not committed to git)
- Environment-based configuration
- Input validation on all endpoints
- SQL injection protection via SQLAlchemy ORM

## 🛣️ Roadmap

- [ ] Slack integration for incident threads
- [ ] Datadog/Grafana metrics integration
- [ ] OpenTelemetry trace correlation
- [ ] Kubernetes event ingestion
- [ ] Webhook support for real-time updates
- [ ] Advanced RAG with fine-tuning
- [ ] Evaluation harness for ML models
- [ ] Role-based access control
- [ ] Audit logging
- [ ] Multi-tenant support

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Hugging Face](https://huggingface.co/) for ML model hosting
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent framework
- [Next.js](https://nextjs.org/) for the React framework
- [pgvector](https://github.com/pgvector/pgvector) for vector similarity search

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ for on-call engineers everywhere**
