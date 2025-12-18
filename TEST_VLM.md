# Testing VLM (Vision-Language Model) Integration

## Overview

OpsLens uses Vision-Language Models (VLM) to analyze dashboard screenshots and extract insights. The VLM can identify errors, anomalies, metrics, and important information from images.

## Quick Test

### 1. Check VLM Status

```bash
curl http://localhost:8000/api/v1/test/vlm/status
```

Expected response:
```json
{
  "api_key_configured": true,
  "model": "Qwen/Qwen2-VL-2B-Instruct",
  "api_url": "https://api-inference.huggingface.co",
  "status": "ready"
}
```

### 2. Test VLM with an Image

```bash
curl -X POST http://localhost:8000/api/v1/test/vlm \
  -F "file=@/path/to/your/screenshot.png"
```

This will test the VLM with multiple prompts and return detailed results.

## Testing via UI

1. **Create or open an incident** at http://localhost:3000
2. **Go to the Evidence tab**
3. **Click "Upload Screenshot"** (if available) or use the API
4. **Upload a dashboard screenshot**
5. **Wait a few seconds** for processing
6. **View the VLM analysis** in the evidence content

## Testing via API

### Upload Screenshot to Incident

```bash
# First, get an incident ID
INCIDENT_ID=$(curl -s http://localhost:8000/api/v1/incidents | jq -r '.[0].id')

# Upload screenshot
curl -X POST http://localhost:8000/api/v1/evidence/incident/$INCIDENT_ID/upload-screenshot \
  -F "file=@/path/to/screenshot.png"
```

The screenshot will be:
1. Saved to the artifacts directory
2. Processed by VLM asynchronously
3. Analysis added to evidence content
4. Embedding generated for RAG search

### Check Processing Status

```bash
# Get evidence items for incident
curl http://localhost:8000/api/v1/evidence/incident/$INCIDENT_ID
```

Look for evidence items with `evidence_type: "screenshot"` and check if `content` field has VLM analysis.

## What the VLM Analyzes

The VLM is prompted to:
- Describe what it sees in the dashboard
- Identify errors or anomalies
- Extract key metrics and their values
- Summarize important information

## Example Screenshots to Test

Good test images:
- Grafana dashboards with metrics
- Datadog error graphs
- AWS CloudWatch dashboards
- Kubernetes dashboard screenshots
- Application error screens
- Any monitoring/observability dashboard

## Troubleshooting

### VLM Not Working

1. **Check API Key:**
   ```bash
   curl http://localhost:8000/api/v1/test/vlm/status
   ```
   Ensure `api_key_configured` is `true`

2. **Check Model Availability:**
   - The model might be loading (first request can take 30-60 seconds)
   - Hugging Face free tier has rate limits
   - Check Hugging Face model page: https://huggingface.co/Qwen/Qwen2-VL-2B-Instruct

3. **Check Logs:**
   ```bash
   docker-compose logs backend | grep -i vlm
   docker-compose logs celery-worker | grep -i vlm
   ```

4. **Test Directly:**
   ```bash
   # Test endpoint with a simple image
   curl -X POST http://localhost:8000/api/v1/test/vlm \
     -F "file=@test_image.png" | jq
   ```

### Common Issues

**"Model is loading" error:**
- Wait 30-60 seconds and try again
- First request to a model loads it into memory

**"Rate limit exceeded":**
- Hugging Face free tier has limits
- Wait a few minutes between requests
- Consider upgrading to paid tier for production

**"Invalid image format":**
- Ensure image is in supported format (PNG, JPEG, etc.)
- Check file size (should be < 10MB)

**"No analysis generated":**
- Check Celery worker is running: `docker-compose ps celery-worker`
- Check worker logs for errors
- Verify image was saved correctly

## Integration into Your Systems

### For Developers

1. **Use the API endpoint:**
   ```python
   import requests
   
   incident_id = "your-incident-id"
   with open("screenshot.png", "rb") as f:
       response = requests.post(
           f"http://localhost:8000/api/v1/evidence/incident/{incident_id}/upload-screenshot",
           files={"file": f}
       )
   ```

2. **Check processing status:**
   ```python
   evidence_id = response.json()["id"]
   # Poll for completion
   while True:
       evidence = requests.get(f"http://localhost:8000/api/v1/evidence/{evidence_id}").json()
       if evidence.get("content"):
           print("VLM analysis:", evidence["content"])
           break
       time.sleep(2)
   ```

3. **Webhook Integration:**
   - Set up webhooks in your monitoring tools
   - Send screenshots automatically when alerts fire
   - OpsLens will process them asynchronously

### For Operations Teams

1. **Manual Upload:**
   - Use the UI to upload screenshots during incidents
   - VLM analysis appears automatically

2. **Automated Capture:**
   - Configure monitoring tools to capture screenshots
   - Send to OpsLens API automatically
   - Get AI-powered insights without manual analysis

## Model Configuration

Default model: `Qwen/Qwen2-VL-2B-Instruct`

To change the model, update `VLM_MODEL` in `backend/app/config.py` or set environment variable.

Supported models:
- `Qwen/Qwen2-VL-2B-Instruct` (default, fast, good quality)
- `Qwen/Qwen2-VL-7B-Instruct` (better quality, slower)
- Other Hugging Face vision-language models

## Performance

- **Processing time:** 5-30 seconds per image (depends on model and image size)
- **Concurrent processing:** Handled by Celery workers
- **Rate limits:** Depends on Hugging Face API tier
- **Cost:** Free tier available, paid tiers for production use

## Next Steps

- [ ] Test with your own dashboard screenshots
- [ ] Integrate with your monitoring tools
- [ ] Set up automated screenshot capture
- [ ] Fine-tune prompts for your use case
- [ ] Consider self-hosting models for better performance

