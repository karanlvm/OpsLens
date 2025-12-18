from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
from app.db import Base


class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="open")  # open, investigating, resolved, closed
    severity = Column(String(20), default="medium")  # low, medium, high, critical
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    timeline_events = relationship("TimelineEvent", back_populates="incident", cascade="all, delete-orphan")
    hypotheses = relationship("Hypothesis", back_populates="incident", cascade="all, delete-orphan")
    evidence_items = relationship("EvidenceItem", back_populates="incident", cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="incident", cascade="all, delete-orphan")
    
    # Metadata (renamed to avoid SQLAlchemy reserved word conflict)
    incident_metadata = Column(JSON, default=dict)


class TimelineEvent(Base):
    __tablename__ = "timeline_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_type = Column(String(100), nullable=False)  # alert, deployment, log_error, metric_spike, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text)
    source = Column(String(100))  # pagerduty, github, grafana, etc.
    source_id = Column(String(255))  # External ID from source system
    event_metadata = Column(JSON, default=dict)
    
    # Relationships
    incident = relationship("Incident", back_populates="timeline_events")


class Hypothesis(Base):
    __tablename__ = "hypotheses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)  # 0.0 to 1.0
    rank = Column(Integer, default=0)
    status = Column(String(50), default="pending")  # pending, investigating, confirmed, rejected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Evidence links
    supporting_evidence = Column(JSON, default=list)  # List of evidence item IDs
    
    # Relationships
    incident = relationship("Incident", back_populates="hypotheses")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    evidence_type = Column(String(50), nullable=False)  # log, metric, screenshot, trace, pr, etc.
    title = Column(String(255), nullable=False)
    content = Column(Text)
    source = Column(String(100))
    source_url = Column(String(500))
    file_path = Column(String(500))  # For screenshots/artifacts
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Embedding for RAG
    embedding = Column(Vector(1024), nullable=True)  # BGE-M3 produces 1024-dim vectors
    
    # Relationships
    incident = relationship("Incident", back_populates="evidence_items")


class Action(Base):
    __tablename__ = "actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    action_type = Column(String(50))  # query, page, rollback, etc.
    status = Column(String(50), default="pending")  # pending, in_progress, completed, skipped
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    incident = relationship("Incident", back_populates="actions")


class Runbook(Base):
    __tablename__ = "runbooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    content = Column(Text, nullable=False)  # Markdown content
    service = Column(String(100))
    tags = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Embedding for RAG
    embedding = Column(Vector(1024), nullable=True)


class Postmortem(Base):
    __tablename__ = "postmortems"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text)
    root_cause = Column(Text)
    contributing_factors = Column(JSON, default=list)
    timeline = Column(JSON, default=list)
    impact = Column(Text)
    resolution = Column(Text)
    follow_ups = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

