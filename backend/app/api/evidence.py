from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.db import get_db
from app.db.models import EvidenceItem, Incident
from pydantic import BaseModel
from datetime import datetime
import os
from app.config import settings

router = APIRouter()


class EvidenceItemResponse(BaseModel):
    id: UUID
    evidence_type: str
    title: str
    content: Optional[str]
    source: Optional[str]
    source_url: Optional[str]
    file_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class EvidenceItemCreate(BaseModel):
    evidence_type: str
    title: str
    content: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None


@router.get("/incident/{incident_id}", response_model=List[EvidenceItemResponse])
async def get_incident_evidence(
    incident_id: UUID,
    evidence_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all evidence items for an incident."""
    query = db.query(EvidenceItem).filter(EvidenceItem.incident_id == incident_id)
    if evidence_type:
        query = query.filter(EvidenceItem.evidence_type == evidence_type)
    
    evidence = query.order_by(EvidenceItem.created_at.desc()).all()
    return evidence


@router.get("/{evidence_id}", response_model=EvidenceItemResponse)
async def get_evidence(evidence_id: UUID, db: Session = Depends(get_db)):
    """Get a specific evidence item."""
    evidence = db.query(EvidenceItem).filter(EvidenceItem.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


@router.post("/incident/{incident_id}", response_model=EvidenceItemResponse)
async def create_evidence(
    incident_id: UUID,
    evidence: EvidenceItemCreate,
    db: Session = Depends(get_db)
):
    """Create a new evidence item."""
    # Verify incident exists
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    db_evidence = EvidenceItem(
        incident_id=incident_id,
        evidence_type=evidence.evidence_type,
        title=evidence.title,
        content=evidence.content,
        source=evidence.source,
        source_url=evidence.source_url
    )
    db.add(db_evidence)
    db.commit()
    db.refresh(db_evidence)
    
    # Process evidence asynchronously (generate embedding, analyze with VLM if screenshot, etc.)
    from app.workers.evidence_worker import process_evidence
    process_evidence.delay(str(db_evidence.id))
    
    return db_evidence


@router.post("/incident/{incident_id}/upload-screenshot", response_model=EvidenceItemResponse)
async def upload_screenshot(
    incident_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a screenshot and process it with VLM."""
    # Verify incident exists
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Save file
    os.makedirs(settings.ARTIFACTS_DIR, exist_ok=True)
    file_path = os.path.join(settings.ARTIFACTS_DIR, f"{incident_id}_{file.filename}")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create evidence item
    db_evidence = EvidenceItem(
        incident_id=incident_id,
        evidence_type="screenshot",
        title=f"Screenshot: {file.filename}",
        file_path=file_path
    )
    db.add(db_evidence)
    db.commit()
    db.refresh(db_evidence)
    
    # Process with VLM
    from app.workers.evidence_worker import process_screenshot
    process_screenshot.delay(str(db_evidence.id))
    
    return db_evidence

