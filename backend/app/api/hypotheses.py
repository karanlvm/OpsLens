from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.db import get_db
from app.db.models import Hypothesis, Incident
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class HypothesisResponse(BaseModel):
    id: UUID
    title: str
    description: str
    confidence: float
    rank: int
    status: str
    supporting_evidence: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/incident/{incident_id}", response_model=List[HypothesisResponse])
async def get_incident_hypotheses(incident_id: UUID, db: Session = Depends(get_db)):
    """Get all hypotheses for an incident, ranked by confidence."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    hypotheses = db.query(Hypothesis).filter(
        Hypothesis.incident_id == incident_id
    ).order_by(Hypothesis.rank.asc(), Hypothesis.confidence.desc()).all()
    
    return hypotheses


@router.get("/{hypothesis_id}", response_model=HypothesisResponse)
async def get_hypothesis(hypothesis_id: UUID, db: Session = Depends(get_db)):
    """Get a specific hypothesis."""
    hypothesis = db.query(Hypothesis).filter(Hypothesis.id == hypothesis_id).first()
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    return hypothesis


@router.patch("/{hypothesis_id}/status")
async def update_hypothesis_status(
    hypothesis_id: UUID,
    status: str,
    db: Session = Depends(get_db)
):
    """Update the status of a hypothesis."""
    hypothesis = db.query(Hypothesis).filter(Hypothesis.id == hypothesis_id).first()
    if not hypothesis:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    
    hypothesis.status = status
    db.commit()
    db.refresh(hypothesis)
    
    return {"message": "Hypothesis status updated", "hypothesis": hypothesis}

