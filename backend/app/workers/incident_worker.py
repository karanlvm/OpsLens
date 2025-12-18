"""Celery tasks for incident processing."""
from app.celery_app import celery_app
from app.db import SessionLocal
from app.db.models import Incident, TimelineEvent, Hypothesis, Action
from app.services.incident_service import IncidentService
from app.integrations.github import GitHubIntegration
from app.integrations.pagerduty import PagerDutyIntegration
from uuid import UUID
from datetime import datetime
import asyncio


@celery_app.task(name="process_new_incident")
def process_new_incident(incident_id: str):
    """Process a new incident - fetch external data and generate timeline."""
    db = SessionLocal()
    try:
        incident = db.query(Incident).filter(Incident.id == UUID(incident_id)).first()
        if not incident:
            return
        
        # Fetch data from integrations
        github = GitHubIntegration()
        pagerduty = PagerDutyIntegration()
        
        # Get recent GitHub merges (async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            recent_merges = loop.run_until_complete(github.get_recent_merges(hours=24))
        finally:
            loop.close()
        for merge in recent_merges[:5]:  # Limit to 5
            # Parse merged_at timestamp
            merged_at_str = merge.get("merged_at")
            try:
                if merged_at_str:
                    if "Z" in merged_at_str:
                        timestamp = datetime.fromisoformat(merged_at_str.replace("Z", "+00:00"))
                    else:
                        timestamp = datetime.fromisoformat(merged_at_str)
                else:
                    timestamp = datetime.utcnow()
            except:
                timestamp = datetime.utcnow()
            
            repo_name = merge.get("repository", {}).get("full_name") if isinstance(merge.get("repository"), dict) else merge.get("repository")
            if not repo_name and "head" in merge:
                repo_name = merge["head"].get("repo", {}).get("full_name")
            
            event = TimelineEvent(
                incident_id=incident.id,
                timestamp=timestamp,
                event_type="deployment",
                title=f"PR merged: {merge.get('title', merge.get('head', {}).get('ref', 'Unknown'))}",
                description=f"PR #{merge.get('number')} merged in {repo_name or 'repository'}",
                source="github",
                source_id=str(merge.get("id", "")),
                event_metadata={"pr_number": merge.get("number"), "repo": repo_name, "url": merge.get("html_url")}
            )
            db.add(event)
        
        # Get PagerDuty incidents (async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            pd_incidents = loop.run_until_complete(pagerduty.get_incidents(hours=24))
        finally:
            loop.close()
        for pd_incident in pd_incidents[:5]:
            # Parse datetime safely
            created_at_str = pd_incident.get("created_at", "")
            try:
                if created_at_str:
                    # Handle different datetime formats
                    if "Z" in created_at_str:
                        timestamp = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    else:
                        timestamp = datetime.fromisoformat(created_at_str)
                else:
                    timestamp = datetime.utcnow()
            except:
                timestamp = datetime.utcnow()
            
            event = TimelineEvent(
                incident_id=incident.id,
                timestamp=timestamp,
                event_type="alert",
                title=f"PagerDuty: {pd_incident.get('title', 'Unknown')}",
                description=pd_incident.get("description", ""),
                source="pagerduty",
                source_id=pd_incident.get("id", ""),
                event_metadata={"status": pd_incident.get("status"), "severity": pd_incident.get("urgency")}
            )
            db.add(event)
        
        db.commit()
        
        # Trigger timeline generation
        generate_incident_timeline.delay(incident_id)
        
    finally:
        db.close()


@celery_app.task(name="generate_incident_timeline")
def generate_incident_timeline(incident_id: str):
    """Generate a summary timeline for an incident."""
    db = SessionLocal()
    try:
        service = IncidentService(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            events = loop.run_until_complete(service.generate_timeline(UUID(incident_id)))
        finally:
            loop.close()
        # Timeline is already generated from events
        return {"status": "success", "events_count": len(events)}
    finally:
        db.close()


@celery_app.task(name="generate_hypotheses")
def generate_hypotheses(incident_id: str):
    """Generate hypotheses for an incident."""
    db = SessionLocal()
    try:
        service = IncidentService(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            hypotheses = loop.run_until_complete(service.generate_hypotheses(UUID(incident_id)))
            
            # Generate actions based on hypotheses
            if hypotheses:
                loop.run_until_complete(service.generate_actions(UUID(incident_id)))
        finally:
            loop.close()
        
        return {"status": "success", "hypotheses_count": len(hypotheses)}
    finally:
        db.close()


@celery_app.task(name="generate_postmortem")
def generate_postmortem(incident_id: str):
    """Generate a postmortem draft for an incident."""
    db = SessionLocal()
    try:
        from app.db.models import Postmortem
        from app.services.ml_service import MLService
        
        incident = db.query(Incident).filter(Incident.id == UUID(incident_id)).first()
        if not incident:
            return
        
        # Get timeline
        events = db.query(TimelineEvent).filter(
            TimelineEvent.incident_id == incident.id
        ).order_by(TimelineEvent.timestamp.asc()).all()
        
        timeline_text = "\n".join([
            f"{e.timestamp}: {e.title}"
            for e in events
        ])
        
        # Get hypotheses
        hypotheses = db.query(Hypothesis).filter(
            Hypothesis.incident_id == incident.id
        ).all()
        hypotheses_text = [h.title for h in hypotheses]
        
        # Generate postmortem
        ml_service = MLService()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            postmortem_data = loop.run_until_complete(ml_service.generate_postmortem(
                incident.title,
                timeline_text,
                hypotheses_text,
                resolution=incident.resolved_at.isoformat() if incident.resolved_at else None
            ))
        finally:
            loop.close()
        
        # Create postmortem
        postmortem = Postmortem(
            incident_id=incident.id,
            title=postmortem_data["title"],
            summary=postmortem_data["summary"],
            root_cause=postmortem_data["root_cause"],
            contributing_factors=postmortem_data["contributing_factors"],
            impact=postmortem_data["impact"],
            resolution=postmortem_data["resolution"],
            follow_ups=postmortem_data["follow_ups"]
        )
        
        db.add(postmortem)
        db.commit()
        
        return {"status": "success", "postmortem_id": str(postmortem.id)}
    finally:
        db.close()

