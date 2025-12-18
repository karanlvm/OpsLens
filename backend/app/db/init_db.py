"""Initialize database with schema and extensions."""
from app.db import engine, Base
from app.config import settings
from sqlalchemy import text

# Import all models so they're registered with Base
from app.db.models import (
    Incident, TimelineEvent, Hypothesis, EvidenceItem, 
    Action, Runbook, Postmortem
)


def init_db():
    """Create all tables and enable pgvector extension."""
    # Enable pgvector extension
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


if __name__ == "__main__":
    init_db()

