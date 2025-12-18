"""Service for sending outgoing webhooks."""
import httpx
from typing import List, Dict, Any, Optional
from app.db import SessionLocal
from app.db.models import WebhookEndpoint, Incident
from app.config import settings
import hmac
import hashlib
import json
from datetime import datetime


class WebhookService:
    """Service for sending webhooks to external systems."""
    
    def __init__(self, db: SessionLocal):
        self.db = db
    
    async def send_webhook(
        self,
        url: str,
        payload: Dict[str, Any],
        secret: Optional[str] = None
    ) -> bool:
        """Send a webhook to an external URL."""
        try:
            headers = {"Content-Type": "application/json"}
            
            # Add signature if secret provided
            if secret:
                payload_str = json.dumps(payload, sort_keys=True)
                signature = hmac.new(
                    secret.encode(),
                    payload_str.encode(),
                    hashlib.sha256
                ).hexdigest()
                headers["X-Webhook-Signature"] = f"sha256={signature}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return True
        except Exception as e:
            print(f"Webhook send failed: {e}")
            return False
    
    async def notify_incident_created(self, incident: Incident):
        """Send webhook when incident is created."""
        # Get all active webhook endpoints for incident.created event
        endpoints = self.db.query(WebhookEndpoint).filter(
            WebhookEndpoint.is_active == True
        ).all()
        
        payload = {
            "event": "incident.created",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "incident_id": str(incident.id),
                "title": incident.title,
                "description": incident.description,
                "severity": incident.severity,
                "status": incident.status,
                "created_at": incident.created_at.isoformat() if incident.created_at else None
            }
        }
        
        for endpoint in endpoints:
            if "incident.created" in (endpoint.events or "").split(","):
                await self.send_webhook(endpoint.url, payload, endpoint.secret)
                # Update last_triggered
                endpoint.last_triggered = datetime.utcnow()
                self.db.commit()
    
    async def notify_incident_updated(self, incident: Incident):
        """Send webhook when incident is updated."""
        endpoints = self.db.query(WebhookEndpoint).filter(
            WebhookEndpoint.is_active == True
        ).all()
        
        payload = {
            "event": "incident.updated",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "incident_id": str(incident.id),
                "title": incident.title,
                "status": incident.status,
                "severity": incident.severity,
                "updated_at": incident.updated_at.isoformat() if incident.updated_at else None
            }
        }
        
        for endpoint in endpoints:
            if "incident.updated" in (endpoint.events or "").split(","):
                await self.send_webhook(endpoint.url, payload, endpoint.secret)
                endpoint.last_triggered = datetime.utcnow()
                self.db.commit()
    
    async def notify_hypothesis_generated(self, incident_id: str, hypothesis_count: int):
        """Send webhook when hypotheses are generated."""
        endpoints = self.db.query(WebhookEndpoint).filter(
            WebhookEndpoint.is_active == True
        ).all()
        
        payload = {
            "event": "hypothesis.generated",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "incident_id": incident_id,
                "hypothesis_count": hypothesis_count
            }
        }
        
        for endpoint in endpoints:
            if "hypothesis.generated" in (endpoint.events or "").split(","):
                await self.send_webhook(endpoint.url, payload, endpoint.secret)
                endpoint.last_triggered = datetime.utcnow()
                self.db.commit()

