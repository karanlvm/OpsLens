"""Service for incident management and state machine."""
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID
from app.db.models import Incident, TimelineEvent, Hypothesis, EvidenceItem, Action
from app.services.ml_service import MLService
from datetime import datetime


class IncidentService:
    """Service for incident management."""
    
    def __init__(self, db: Session):
        self.db = db
        self.ml_service = MLService()
    
    async def process_incident(self, incident_id: UUID):
        """Process a new incident - generate timeline, hypotheses, actions."""
        incident = self.db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return
        
        # Update status
        incident.status = "investigating"
        self.db.commit()
        
        # Generate timeline (async, handled by workers)
        # Generate hypotheses (async, handled by workers)
        # Generate actions (async, handled by workers)
    
    async def generate_timeline(self, incident_id: UUID) -> List[TimelineEvent]:
        """Generate timeline from evidence and external events."""
        incident = self.db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return []
        
        # Get all timeline events
        events = self.db.query(TimelineEvent).filter(
            TimelineEvent.incident_id == incident_id
        ).order_by(TimelineEvent.timestamp.asc()).all()
        
        return events
    
    async def generate_hypotheses(self, incident_id: UUID) -> List[Hypothesis]:
        """Generate hypotheses based on evidence."""
        incident = self.db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return []
        
        # Get all evidence
        evidence = self.db.query(EvidenceItem).filter(
            EvidenceItem.incident_id == incident_id
        ).all()
        
        if not evidence:
            return []
        
        # Summarize evidence
        evidence_text = "\n".join([
            f"{e.evidence_type}: {e.title}\n{e.content or ''}"
            for e in evidence[:10]  # Limit to avoid token limits
        ])
        
        # Generate hypothesis using ML
        hypothesis_data = await self.ml_service.generate_hypothesis(
            incident.title,
            evidence_text
        )
        
        # Create hypothesis
        hypothesis = Hypothesis(
            incident_id=incident_id,
            title=hypothesis_data["title"],
            description=hypothesis_data["description"],
            confidence=hypothesis_data["confidence"],
            rank=1,
            supporting_evidence=[str(e.id) for e in evidence[:3]]
        )
        
        self.db.add(hypothesis)
        self.db.commit()
        self.db.refresh(hypothesis)
        
        return [hypothesis]
    
    async def generate_actions(self, incident_id: UUID) -> List[Action]:
        """Generate actionable next steps."""
        incident = self.db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return []
        
        # Get hypotheses
        hypotheses = self.db.query(Hypothesis).filter(
            Hypothesis.incident_id == incident_id,
            Hypothesis.status == "pending"
        ).all()
        
        if not hypotheses:
            return []
        
        # Generate actions based on top hypothesis
        top_hypothesis = sorted(hypotheses, key=lambda h: h.confidence, reverse=True)[0]
        
        actions = [
            Action(
                incident_id=incident_id,
                title="Investigate root cause",
                description=f"Based on hypothesis: {top_hypothesis.title}",
                action_type="investigation",
                status="pending"
            ),
            Action(
                incident_id=incident_id,
                title="Check service metrics",
                description="Review Grafana/Datadog dashboards",
                action_type="query",
                status="pending"
            ),
            Action(
                incident_id=incident_id,
                title="Review recent deployments",
                description="Check GitHub for recent PRs and deployments",
                action_type="review",
                status="pending"
            )
        ]
        
        for action in actions:
            self.db.add(action)
        
        self.db.commit()
        
        return actions

