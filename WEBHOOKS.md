# Webhooks Guide

OpsLens supports both **incoming** and **outgoing** webhooks for seamless integration with your systems.

## Incoming Webhooks

OpsLens can receive webhooks from external systems to automatically create or update incidents.

### GitHub Webhooks

**Endpoint:** `POST /api/v1/webhooks/github`

**Setup:**
1. Go to your GitHub repository settings
2. Navigate to Webhooks → Add webhook
3. Set Payload URL: `https://your-opslens-domain.com/api/v1/webhooks/github`
4. Content type: `application/json`
5. Events: Select "Pull requests"
6. Add webhook secret (optional, for verification)

**Events Handled:**
- `pull_request` (closed + merged) → Creates deployment timeline event

**Example Payload:**
```json
{
  "action": "closed",
  "pull_request": {
    "id": 123,
    "number": 42,
    "title": "Fix memory leak",
    "merged": true,
    "base": {
      "repo": {
        "full_name": "org/repo"
      }
    }
  }
}
```

### PagerDuty Webhooks

**Endpoint:** `POST /api/v1/webhooks/pagerduty`

**Setup:**
1. Go to PagerDuty → Integrations → Webhooks
2. Create new webhook
3. Set URL: `https://your-opslens-domain.com/api/v1/webhooks/pagerduty`
4. Select events: `incident.triggered`, `incident.resolved`

**Events Handled:**
- `incident.triggered` → Creates new incident in OpsLens
- `incident.resolved` → Updates incident status to resolved

**Example Payload:**
```json
{
  "messages": [
    {
      "event": "incident.triggered",
      "incident": {
        "id": "ABC123",
        "title": "High CPU usage",
        "description": "CPU at 95%",
        "urgency": "high",
        "html_url": "https://pagerduty.com/incidents/ABC123"
      }
    }
  ]
}
```

### Generic Webhooks

**Endpoint:** `POST /api/v1/webhooks/generic`

**Headers:**
- `X-Webhook-Secret`: (Optional) Secret for verification

**Payload Format:**
```json
{
  "title": "Incident Title",
  "description": "Incident description",
  "severity": "high",
  "metadata": {
    "source": "custom-system",
    "custom_field": "value"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "incident_id": "uuid-here"
}
```

## Outgoing Webhooks

OpsLens can send webhooks to your systems when incidents are created or updated.

### Supported Events

- `incident.created` - New incident created
- `incident.updated` - Incident status or details updated
- `hypothesis.generated` - AI-generated hypotheses available
- `timeline.updated` - Timeline events added
- `evidence.added` - New evidence item added

### Webhook Payload Format

```json
{
  "event": "incident.created",
  "timestamp": "2025-12-18T12:00:00Z",
  "data": {
    "incident_id": "uuid",
    "title": "Incident Title",
    "description": "Description",
    "severity": "high",
    "status": "open",
    "created_at": "2025-12-18T12:00:00Z"
  }
}
```

### Setting Up Outgoing Webhooks

**Via API:**
```bash
POST /api/v1/webhooks/endpoints
Content-Type: application/json

{
  "url": "https://your-system.com/webhooks/opslens",
  "secret": "your-webhook-secret",
  "events": "incident.created,incident.updated"
}
```

**Via Database:**
```sql
INSERT INTO webhook_endpoints (url, secret, events, is_active)
VALUES (
  'https://your-system.com/webhooks/opslens',
  'your-secret',
  'incident.created,incident.updated',
  true
);
```

### Webhook Security

All outgoing webhooks include a signature header:

```
X-Webhook-Signature: sha256=<signature>
```

**Verification (Python):**
```python
import hmac
import hashlib
import json

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        json.dumps(payload, sort_keys=True).encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

## Testing Webhooks

### Test Incoming Webhook

```bash
# Test generic webhook
curl -X POST http://localhost:8000/api/v1/webhooks/generic \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Incident",
    "description": "Testing webhook",
    "severity": "medium"
  }'
```

### Test Webhook Endpoint

```bash
curl http://localhost:8000/api/v1/webhooks/test
```

### Simulate GitHub Webhook

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -d '{
    "action": "closed",
    "pull_request": {
      "id": 123,
      "number": 42,
      "title": "Test PR",
      "merged": true,
      "base": {
        "repo": {
          "full_name": "test/repo"
        }
      }
    }
  }'
```

## Integration Examples

### Slack Integration

**Receive OpsLens webhooks in Slack:**
```python
from flask import Flask, request
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = "your-secret"

@app.route('/webhooks/opslens', methods=['POST'])
def opslens_webhook():
    payload = request.json
    signature = request.headers.get('X-Webhook-Signature', '')
    
    # Verify signature
    if not verify_webhook(payload, signature, WEBHOOK_SECRET):
        return "Invalid signature", 401
    
    event = payload['event']
    data = payload['data']
    
    if event == 'incident.created':
        # Send to Slack
        send_slack_message(f"🚨 New incident: {data['title']}")
    
    return "OK", 200
```

### Datadog Integration

**Send Datadog events to OpsLens:**
```python
import requests

def send_to_opslens(event):
    response = requests.post(
        'https://opslens.com/api/v1/webhooks/generic',
        json={
            'title': event['title'],
            'description': event['text'],
            'severity': 'high' if event.get('alert_type') == 'error' else 'medium',
            'metadata': {
                'source': 'datadog',
                'event_id': event['id']
            }
        }
    )
    return response.json()
```

## Best Practices

1. **Always verify webhook signatures** in production
2. **Use HTTPS** for all webhook URLs
3. **Implement idempotency** - handle duplicate webhooks gracefully
4. **Set up retries** for failed webhook deliveries
5. **Monitor webhook health** - track success/failure rates
6. **Rate limiting** - respect rate limits on both sides
7. **Logging** - log all webhook events for debugging

## Troubleshooting

**Webhook not received:**
- Check URL is accessible (not behind firewall)
- Verify webhook secret matches
- Check OpsLens logs: `docker-compose logs backend | grep webhook`

**Webhook received but not processed:**
- Check payload format matches expected schema
- Verify event type is supported
- Check database connection

**Outgoing webhook not sent:**
- Verify webhook endpoint is active in database
- Check target URL is accessible
- Review webhook service logs

## Next Steps

- [ ] Set up GitHub webhook for deployments
- [ ] Configure PagerDuty webhook for incidents
- [ ] Create Slack integration for notifications
- [ ] Set up monitoring for webhook health
- [ ] Implement webhook retry logic

