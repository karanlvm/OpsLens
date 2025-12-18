"""Webhook endpoints for incoming and outgoing webhooks."""
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import hmac
import hashlib
import json
from app.db import SessionLocal
from app.db.models import Incident, TimelineEvent, EvidenceItem
from app.integrations.github import GitHubIntegration
from app.integrations.pagerduty import PagerDutyIntegration
from app.workers.incident_worker import process_new_incident
from datetime import datetime
import uuid

router = APIRouter()


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """Verify webhook signature."""
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)


@router.post("/webhooks/github")
async def github_webhook(request: Request):
    """Handle GitHub webhooks."""
    payload = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    
    # Verify signature (in production, use webhook secret from GitHub)
    # For now, accept all (add proper verification in production)
    
    event_type = request.headers.get("X-GitHub-Event", "")
    data = await request.json()
    
    db = SessionLocal()
    try:
        if event_type == "pull_request" and data.get("action") == "closed":
            # PR merged
            pr = data.get("pull_request", {})
            if pr.get("merged"):
                # Find or create incident related to this PR
                # For now, create a timeline event for all open incidents
                incidents = db.query(Incident).filter(
                    Incident.status.in_(["open", "investigating"])
                ).all()
                
                for incident in incidents:
                    event = TimelineEvent(
                        incident_id=incident.id,
                        timestamp=datetime.utcnow(),
                        event_type="deployment",
                        title=f"PR merged: {pr.get('title', 'Unknown')}",
                        description=f"PR #{pr.get('number')} merged in {pr.get('base', {}).get('repo', {}).get('full_name', 'repository')}",
                        source="github",
                        source_id=str(pr.get("id", "")),
                        event_metadata={
                            "pr_number": pr.get("number"),
                            "repo": pr.get("base", {}).get("repo", {}).get("full_name"),
                            "merged_by": pr.get("merged_by", {}).get("login"),
                            "url": pr.get("html_url")
                        }
                    )
                    db.add(event)
                
                db.commit()
        
        return {"status": "success", "event": event_type}
    finally:
        db.close()


@router.post("/webhooks/pagerduty")
async def pagerduty_webhook(request: Request):
    """Handle PagerDuty webhooks."""
    payload = await request.body()
    data = await request.json()
    
    db = SessionLocal()
    try:
        messages = data.get("messages", [])
        
        for message in messages:
            event_type = message.get("event")
            incident_data = message.get("incident", {})
            
            if event_type == "incident.triggered":
                # Create or update incident in OpsLens
                pd_incident_id = incident_data.get("id")
                
                # Check if incident already exists
                existing = db.query(Incident).filter(
                    Incident.incident_metadata["pagerduty_id"].astext == pd_incident_id
                ).first()
                
                if not existing:
                    # Create new incident
                    incident = Incident(
                        title=incident_data.get("title", "PagerDuty Incident"),
                        description=incident_data.get("description", ""),
                        severity="high" if incident_data.get("urgency") == "high" else "medium",
                        status="open",
                        incident_metadata={
                            "pagerduty_id": pd_incident_id,
                            "pagerduty_url": incident_data.get("html_url"),
                            "service": incident_data.get("service", {}).get("name")
                        }
                    )
                    db.add(incident)
                    db.flush()
                    
                    # Process incident
                    process_new_incident.delay(str(incident.id))
                else:
                    # Update existing incident
                    existing.status = "investigating"
                    db.commit()
            
            elif event_type == "incident.resolved":
                # Resolve incident
                pd_incident_id = incident_data.get("id")
                incident = db.query(Incident).filter(
                    Incident.incident_metadata["pagerduty_id"].astext == pd_incident_id
                ).first()
                
                if incident:
                    incident.status = "resolved"
                    incident.resolved_at = datetime.utcnow()
                    db.commit()
        
        return {"status": "success", "processed": len(messages)}
    finally:
        db.close()


@router.post("/webhooks/generic")
async def generic_webhook(
    request: Request,
    x_webhook_secret: Optional[str] = Header(None)
):
    """Handle generic webhooks from any source."""
    payload = await request.body()
    data = await request.json()
    
    # Verify webhook secret if provided
    if x_webhook_secret:
        # In production, validate against database
        pass
    
    db = SessionLocal()
    try:
        # Extract incident data from webhook
        title = data.get("title") or data.get("incident_title") or "Webhook Incident"
        description = data.get("description") or data.get("message", "")
        severity = data.get("severity", "medium")
        
        # Create incident
        incident = Incident(
            title=title,
            description=description,
            severity=severity,
            status="open",
            incident_metadata={
                "source": "webhook",
                "webhook_data": data
            }
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        
        # Process incident
        process_new_incident.delay(str(incident.id))
        
        return {"status": "success", "incident_id": str(incident.id)}
    finally:
        db.close()


@router.get("/webhooks/test")
async def test_webhook():
    """Test webhook endpoint."""
    return {
        "status": "ok",
        "message": "Webhook endpoint is working",
        "endpoints": {
            "github": "/api/v1/webhooks/github",
            "pagerduty": "/api/v1/webhooks/pagerduty",
            "generic": "/api/v1/webhooks/generic"
        }
    }

