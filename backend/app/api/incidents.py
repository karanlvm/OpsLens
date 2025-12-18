from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.db import get_db
from app.db.models import Incident, TimelineEvent, Hypothesis, Action
from app.services.incident_service import IncidentService
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class IncidentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str = "medium"


class IncidentResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    status: str
    severity: str
    created_at: datetime
    updated_at: Optional[datetime]
    resolved_at: Optional[datetime]
    incident_metadata: dict

    class Config:
        from_attributes = True


class TimelineEventResponse(BaseModel):
    id: UUID
    timestamp: datetime
    event_type: str
    title: str
    description: Optional[str]
    source: Optional[str]
    event_metadata: dict

    class Config:
        from_attributes = True


@router.get("/", response_model=List[IncidentResponse])
async def list_incidents(
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all incidents, optionally filtered by status."""
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    incidents = query.order_by(Incident.created_at.desc()).limit(limit).all()
    return incidents


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: UUID, db: Session = Depends(get_db)):
    """Get a specific incident by ID."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/", response_model=IncidentResponse)
async def create_incident(
    incident: IncidentCreate,
    db: Session = Depends(get_db)
):
    """Create a new incident."""
    db_incident = Incident(
        title=incident.title,
        description=incident.description,
        severity=incident.severity
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    
    # Trigger async processing
    from app.workers.incident_worker import process_new_incident
    process_new_incident.delay(str(db_incident.id))
    
    # Send webhook notification
    try:
        from app.services.webhook_service import WebhookService
        webhook_service = WebhookService(db)
        await webhook_service.notify_incident_created(db_incident)
    except Exception as e:
        print(f"Webhook notification failed: {e}")
    
    return db_incident


@router.get("/{incident_id}/timeline", response_model=List[TimelineEventResponse])
async def get_incident_timeline(incident_id: UUID, db: Session = Depends(get_db)):
    """Get timeline events for an incident."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    events = db.query(TimelineEvent).filter(
        TimelineEvent.incident_id == incident_id
    ).order_by(TimelineEvent.timestamp.asc()).all()
    
    return events


@router.post("/{incident_id}/generate-timeline")
async def generate_timeline(incident_id: UUID, db: Session = Depends(get_db)):
    """Manually trigger timeline generation for an incident."""
    from app.workers.incident_worker import generate_incident_timeline
    generate_incident_timeline.delay(str(incident_id))
    return {"message": "Timeline generation started"}


@router.post("/{incident_id}/generate-hypotheses")
async def generate_hypotheses(incident_id: UUID, db: Session = Depends(get_db)):
    """Manually trigger hypothesis generation for an incident."""
    from app.workers.incident_worker import generate_hypotheses
    generate_hypotheses.delay(str(incident_id))
    return {"message": "Hypothesis generation started"}


@router.post("/{incident_id}/generate-postmortem")
async def generate_postmortem(incident_id: UUID, db: Session = Depends(get_db)):
    """Generate a postmortem draft for an incident."""
    from app.workers.incident_worker import generate_postmortem
    generate_postmortem.delay(str(incident_id))
    return {"message": "Postmortem generation started"}

