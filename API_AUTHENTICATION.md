# API Authentication Guide

OpsLens supports API key authentication for securing your REST API endpoints.

## Authentication Methods

### 1. API Key (Recommended)

**Header:**
```
X-API-Key: your-api-key-here
```

**Query Parameter:**
```
?api_key=your-api-key-here
```

### 2. OAuth2 Token (Coming Soon)

**Header:**
```
Authorization: Bearer your-token-here
```

## Getting Started

### Development Mode (No Auth)

By default, authentication is **disabled** for development. All endpoints are accessible without authentication.

### Production Mode (Auth Required)

To enable authentication:

1. **Set environment variable:**
   ```bash
   ENABLE_AUTH=true
   ```

2. **Or update config:**
   ```python
   # backend/app/config.py
   ENABLE_AUTH: bool = True
   ```

3. **Restart backend:**
   ```bash
   docker-compose restart backend
   ```

## Creating API Keys

### Via API

```bash
POST /api/v1/auth/api-keys
Content-Type: application/json

{
  "name": "My Integration",
  "expires_days": 90
}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "My Integration",
  "key": "generated-api-key-here",  // Only shown once!
  "created_at": "2025-12-18T12:00:00Z",
  "expires_at": "2025-03-18T12:00:00Z"
}
```

**⚠️ Important:** Save the API key immediately - it's only shown once!

### Via Database

```sql
INSERT INTO api_keys (key_hash, name, is_active)
VALUES (
  '<hashed-key>',
  'My Integration',
  true
);
```

## Using API Keys

### cURL Example

```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/api/v1/incidents
```

### Python Example

```python
import requests

headers = {
    "X-API-Key": "your-api-key",
    "Content-Type": "application/json"
}

response = requests.get(
    "http://localhost:8000/api/v1/incidents",
    headers=headers
)
```

### JavaScript Example

```javascript
fetch('http://localhost:8000/api/v1/incidents', {
  headers: {
    'X-API-Key': 'your-api-key'
  }
})
```

## Verifying API Key

```bash
GET /api/v1/auth/verify
Headers:
  X-API-Key: your-api-key
```

**Response:**
```json
{
  "status": "valid",
  "message": "API key is valid"
}
```

## Protected Endpoints

When `ENABLE_AUTH=true`, these endpoints require authentication:

- `GET /api/v1/incidents` - List incidents
- `POST /api/v1/incidents` - Create incident
- `GET /api/v1/incidents/{id}` - Get incident
- `POST /api/v1/evidence/*` - Evidence operations
- `GET /api/v1/hypotheses/*` - Hypothesis operations
- `GET /api/v1/runbooks/*` - Runbook operations
- `POST /api/v1/test/vlm` - VLM testing

## Public Endpoints (No Auth Required)

These endpoints are always public:

- `GET /` - API info
- `GET /health` - Health check
- `POST /api/v1/webhooks/*` - Webhook endpoints
- `POST /api/v1/auth/token` - Get OAuth2 token
- `POST /api/v1/auth/api-keys` - Create API key (may require auth in production)

## Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** for API keys
3. **Rotate keys regularly** (every 90 days)
4. **Use different keys** for different integrations
5. **Revoke compromised keys** immediately
6. **Use HTTPS** in production
7. **Implement rate limiting** per API key
8. **Monitor API key usage** for anomalies

## Rate Limiting

Each API key has a rate limit (default: 1000 requests/hour). This can be configured per key in the database.

## Error Responses

### Missing API Key

```json
{
  "detail": "API key required. Provide X-API-Key header or api_key query parameter."
}
```

**Status:** 401 Unauthorized

### Invalid API Key

```json
{
  "detail": "Invalid API key"
}
```

**Status:** 401 Unauthorized

### Expired API Key

```json
{
  "detail": "API key has expired"
}
```

**Status:** 401 Unauthorized

## Managing API Keys

### List API Keys

```sql
SELECT id, name, is_active, created_at, expires_at, last_used
FROM api_keys
ORDER BY created_at DESC;
```

### Revoke API Key

```sql
UPDATE api_keys
SET is_active = false
WHERE id = 'key-uuid';
```

### Update Rate Limit

```sql
UPDATE api_keys
SET rate_limit = 2000
WHERE id = 'key-uuid';
```

## Integration Examples

### GitHub Actions

```yaml
- name: Create Incident
  run: |
    curl -X POST ${{ secrets.OPSLENS_URL }}/api/v1/incidents \
      -H "X-API-Key: ${{ secrets.OPSLENS_API_KEY }}" \
      -H "Content-Type: application/json" \
      -d '{"title": "Deployment failed", "severity": "high"}'
```

### Datadog Integration

```python
import os
import requests

OPSLENS_API_KEY = os.getenv('OPSLENS_API_KEY')
OPSLENS_URL = os.getenv('OPSLENS_URL', 'https://opslens.com')

def create_incident(title, description, severity='medium'):
    response = requests.post(
        f'{OPSLENS_URL}/api/v1/incidents',
        headers={
            'X-API-Key': OPSLENS_API_KEY,
            'Content-Type': 'application/json'
        },
        json={
            'title': title,
            'description': description,
            'severity': severity
        }
    )
    return response.json()
```

## Troubleshooting

**"API key required" error:**
- Check `ENABLE_AUTH` is set correctly
- Verify API key is in header or query parameter
- Check API key format (no extra spaces)

**"Invalid API key" error:**
- Verify key is correct
- Check key is active in database
- Ensure key hasn't expired

**Rate limit exceeded:**
- Wait for rate limit window to reset
- Request higher rate limit
- Use multiple API keys for different services

## Next Steps

- [ ] Set up API key management UI
- [ ] Implement OAuth2 flow
- [ ] Add JWT token support
- [ ] Set up API key rotation
- [ ] Add usage analytics
- [ ] Implement IP whitelisting

