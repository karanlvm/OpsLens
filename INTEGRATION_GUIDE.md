# Integration Guide for OpsLens

This guide helps you integrate OpsLens into your existing systems and workflows.

## Overview

OpsLens provides REST APIs and webhooks (coming soon) to integrate with:
- Monitoring tools (Datadog, Grafana, CloudWatch)
- Incident management (PagerDuty, Opsgenie)
- Version control (GitHub, GitLab)
- Communication (Slack, Microsoft Teams)
- Observability (OpenTelemetry, Jaeger)

## Quick Integration Checklist

- [ ] Set up OpsLens (see README.md)
- [ ] Configure API keys in `secrets.env`
- [ ] Test integrations (see below)
- [ ] Set up webhooks or polling
- [ ] Configure automated screenshot capture
- [ ] Train team on using OpsLens

## API Integration

### Base URL

```
http://localhost:8000/api/v1  # Development
https://your-domain.com/api/v1  # Production
```

### Authentication

Currently, OpsLens runs in development mode without authentication. For production:
- Add API key authentication
- Implement OAuth2
- Use JWT tokens

### Creating Incidents

```bash
POST /api/v1/incidents
Content-Type: application/json

{
  "title": "High error rate in payment service",
  "description": "Error rate increased to 5%",
  "severity": "high"
}
```

### Uploading Screenshots

```bash
POST /api/v1/evidence/incident/{incident_id}/upload-screenshot
Content-Type: multipart/form-data

file: <screenshot.png>
```

The VLM will automatically analyze the screenshot and add insights to the evidence.

### Adding Evidence

```bash
POST /api/v1/evidence/incident/{incident_id}
Content-Type: application/json

{
  "evidence_type": "log",
  "title": "Application logs",
  "content": "Error logs from payment service...",
  "source": "datadog"
}
```

## Integration Patterns

### 1. PagerDuty Integration

**Current:** OpsLens fetches incidents from PagerDuty API

**Future:** Webhook integration
```python
# PagerDuty webhook → OpsLens
# Automatically create incidents when PagerDuty alerts fire
```

### 2. GitHub Integration

**Current:** OpsLens fetches recent PR merges

**Future:** Webhook integration
```python
# GitHub webhook → OpsLens
# Automatically add deployment events to incidents
```

### 3. Monitoring Tools

**Pattern:** Automated screenshot capture + upload

```python
# Example: Datadog screenshot capture
import requests
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1 import DashboardsApi

# Capture dashboard screenshot
screenshot = capture_dashboard_screenshot(dashboard_id)

# Upload to OpsLens
incident_id = create_incident("High CPU alert")
upload_screenshot(incident_id, screenshot)
```

### 4. Slack Integration

**Pattern:** Incident updates via Slack

```python
# OpsLens → Slack webhook
# Post incident updates, hypotheses, actions to Slack channel
```

## VLM Integration

### Use Cases

1. **Dashboard Analysis**
   - Capture Grafana/Datadog dashboards on alerts
   - Upload to OpsLens for AI analysis
   - Get insights without manual review

2. **Error Screenshot Analysis**
   - Capture application error screens
   - VLM identifies error types and patterns
   - Correlate with logs and metrics

3. **Deployment Verification**
   - Capture deployment dashboards
   - Verify metrics after deployment
   - Detect anomalies automatically

### Integration Example

```python
import requests
from PIL import Image
import io

def analyze_dashboard_screenshot(dashboard_url, incident_id):
    # Capture screenshot (using selenium, playwright, etc.)
    screenshot = capture_screenshot(dashboard_url)
    
    # Upload to OpsLens
    response = requests.post(
        f"http://localhost:8000/api/v1/evidence/incident/{incident_id}/upload-screenshot",
        files={"file": ("screenshot.png", screenshot, "image/png")}
    )
    
    evidence_id = response.json()["id"]
    
    # Poll for VLM analysis
    while True:
        evidence = requests.get(
            f"http://localhost:8000/api/v1/evidence/{evidence_id}"
        ).json()
        
        if evidence.get("content"):
            analysis = evidence["content"]
            print(f"VLM Analysis: {analysis}")
            return analysis
        
        time.sleep(2)
```

## Webhook Integration (Coming Soon)

### Incoming Webhooks

OpsLens will accept webhooks from:
- PagerDuty (incident creation/updates)
- GitHub (PR merges, deployments)
- Slack (incident threads)
- Monitoring tools (alerts, metrics)

### Outgoing Webhooks

OpsLens will send webhooks to:
- Slack (incident updates)
- Teams (notifications)
- Custom endpoints (your systems)

## Best Practices

1. **Automate Everything**
   - Set up automated screenshot capture
   - Use webhooks instead of polling
   - Integrate with CI/CD pipelines

2. **Error Handling**
   - Implement retries for API calls
   - Handle rate limits gracefully
   - Log all integration errors

3. **Security**
   - Use API keys for authentication
   - Validate webhook signatures
   - Encrypt sensitive data

4. **Monitoring**
   - Monitor integration health
   - Track API usage
   - Alert on integration failures

## Testing Your Integration

1. **Test VLM:**
   ```bash
   curl http://localhost:8000/api/v1/test/vlm/status
   ```

2. **Test Integrations:**
   ```bash
   curl http://localhost:8000/api/v1/integrations/test/all
   ```

3. **Test API:**
   ```bash
   # Create test incident
   curl -X POST http://localhost:8000/api/v1/incidents \
     -H "Content-Type: application/json" \
     -d '{"title": "Test Incident", "severity": "low"}'
   ```

## Support

For integration help:
- Check API documentation: http://localhost:8000/docs
- Review test endpoints
- Open an issue on GitHub
- Check integration logs: `docker-compose logs backend`

## Next Steps

1. Set up your first integration
2. Test with real data
3. Automate screenshot capture
4. Configure webhooks (when available)
5. Train your team

