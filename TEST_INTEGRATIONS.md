# Testing GitHub and PagerDuty Integrations

## Quick Test

You can test the integrations using the API endpoints:

### Test GitHub Integration
```bash
curl http://localhost:8000/api/v1/integrations/test/github | python3 -m json.tool
```

### Test PagerDuty Integration
```bash
curl http://localhost:8000/api/v1/integrations/test/pagerduty | python3 -m json.tool
```

### Test All Integrations
```bash
curl http://localhost:8000/api/v1/integrations/test/all | python3 -m json.tool
```

## Testing with Real Incidents

1. **Create a new incident** via the API or UI
2. **Trigger timeline generation** - this will fetch real data from GitHub and PagerDuty
3. **Check the timeline** - you should see:
   - Recent GitHub PR merges (if any in the last 24 hours)
   - Recent PagerDuty incidents (if any)

## What Gets Fetched

### GitHub
- Recent merged PRs from your repositories (last 24 hours)
- PR details including title, number, repository, and merge timestamp
- Automatically added to incident timeline as "deployment" events

### PagerDuty
- Recent incidents (last 24 hours) with status "triggered" or "acknowledged"
- Incident details including title, description, status, and timestamp
- Automatically added to incident timeline as "alert" events

## Troubleshooting

### GitHub Issues
- **No PRs found**: This is normal if you haven't merged any PRs in the last 24 hours
- **401 Unauthorized**: Check your GitHub API key in `secrets.env`
- **403 Forbidden**: Make sure your token has `repo` scope

### PagerDuty Issues
- **No incidents found**: This is normal if you don't have any active incidents
- **401 Unauthorized**: Check your PagerDuty API key and email in `secrets.env`
- **403 Forbidden**: Make sure your API key has the right permissions

## API Keys Setup

Make sure your `secrets.env` has:
```bash
GITHUB_API_KEY=your_token_here
GITHUB_ORG=your_username_or_org
PAGERDUTY_API_KEY=your_key_here
PAGERDUTY_EMAIL=your_email@example.com
```

## Viewing Integration Data

After creating an incident and generating the timeline, you can:
1. Go to the incident detail page
2. Click on the "Timeline" tab
3. You should see events from GitHub and PagerDuty with:
   - Correct timestamps
   - Source information
   - Links to the original items (in metadata)

