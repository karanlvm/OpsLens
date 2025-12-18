# Quick Start Guide

## Prerequisites

1. **Docker Desktop** - Make sure it's installed and running
2. **API Keys** - You'll need:
   - Hugging Face API key (free): https://huggingface.co/settings/tokens
   - GitHub Personal Access Token: https://github.com/settings/tokens (needs `repo` scope)
   - PagerDuty API key: From your PagerDuty account settings

## Setup Steps

1. **Clone/Navigate to the project:**
   ```bash
   cd OpsLens
   ```

2. **Run setup script:**
   ```bash
   ./setup.sh
   ```
   
   Or manually:
   ```bash
   # Copy secrets template
   cp secrets.env.example secrets.env
   
   # Edit secrets.env and add your API keys
   nano secrets.env  # or use your preferred editor
   
   # Start services
   docker-compose up -d
   
   # Initialize database
   docker-compose exec backend python -m app.db.init_db
   
   # Generate synthetic data (optional but recommended for demo)
   docker-compose exec backend python -m app.data.generate_synthetic
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Using the Application

### View Incidents
- Navigate to http://localhost:3000
- You'll see a list of incidents (if you generated synthetic data)

### Incident Details
- Click on any incident to view details
- The incident page has 4 tabs:
  - **Timeline**: Chronological events related to the incident
  - **Hypotheses**: AI-generated root cause hypotheses
  - **Evidence**: Logs, metrics, screenshots, etc.
  - **Actions**: Actionable next steps

### Generate AI Insights
- Click "Generate Timeline" to fetch data from GitHub and PagerDuty
- Click "Generate Hypotheses" to create root cause hypotheses based on evidence

### Upload Screenshots
- Go to the Evidence tab
- Upload a dashboard screenshot
- The VLM will analyze it and extract insights

## Troubleshooting

### Services won't start
- Check Docker Desktop is running
- Check ports 3000, 8000, 5432, 6379 are not in use
- Check `docker-compose logs` for errors

### Database errors
- Make sure Postgres container is healthy: `docker-compose ps`
- Reinitialize: `docker-compose exec backend python -m app.db.init_db`

### API key errors
- Verify your API keys in `secrets.env`
- For Hugging Face, make sure the token has read access
- For GitHub, ensure the token has `repo` scope

### Frontend not loading
- Check backend is running: `curl http://localhost:8000/health`
- Check frontend logs: `docker-compose logs frontend`

## Development

### View logs
```bash
docker-compose logs -f [service_name]
# e.g., docker-compose logs -f backend
```

### Restart a service
```bash
docker-compose restart [service_name]
```

### Stop everything
```bash
docker-compose down
```

### Clean restart (removes volumes)
```bash
docker-compose down -v
docker-compose up -d
```

## Next Steps

- Explore the API documentation at http://localhost:8000/docs
- Try creating a new incident via the API
- Upload a screenshot to test VLM functionality
- Search runbooks using the RAG system

