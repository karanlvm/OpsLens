from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.db import get_db
from app.db.models import Action, Incident, Runbook
from app.services.rag_service import RAGService
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class ActionResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    action_type: Optional[str]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class RunbookResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    content: str
    service: Optional[str]
    tags: List[str]

    class Config:
        from_attributes = True


@router.get("/incident/{incident_id}/actions", response_model=List[ActionResponse])
async def get_incident_actions(incident_id: UUID, db: Session = Depends(get_db)):
    """Get all actions for an incident."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    actions = db.query(Action).filter(
        Action.incident_id == incident_id
    ).order_by(Action.created_at.asc()).all()
    
    return actions


@router.post("/incident/{incident_id}/actions/{action_id}/complete")
async def complete_action(
    incident_id: UUID,
    action_id: UUID,
    db: Session = Depends(get_db)
):
    """Mark an action as completed."""
    action = db.query(Action).filter(
        Action.id == action_id,
        Action.incident_id == incident_id
    ).first()
    
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    action.status = "completed"
    action.completed_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Action completed", "action": action}


@router.get("/search", response_model=List[RunbookResponse])
async def search_runbooks(
    query: str,
    service: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Search runbooks using RAG."""
    rag_service = RAGService(db)
    runbooks = await rag_service.search_runbooks(query, service=service, limit=limit)
    return runbooks

