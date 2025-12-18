"""Celery tasks for evidence processing."""
from app.celery_app import celery_app
from app.db import SessionLocal
from app.db.models import EvidenceItem
from app.services.ml_service import MLService
from app.services.rag_service import RAGService
from uuid import UUID
import os
import asyncio


@celery_app.task(name="process_evidence")
def process_evidence(evidence_id: str):
    """Process evidence item - generate embedding for RAG."""
    db = SessionLocal()
    try:
        evidence = db.query(EvidenceItem).filter(EvidenceItem.id == UUID(evidence_id)).first()
        if not evidence:
            return
        
        # Generate embedding if content exists
        if evidence.content:
            rag_service = RAGService(db)
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(rag_service.index_evidence(evidence))
            finally:
                loop.close()
        
        return {"status": "success"}
    finally:
        db.close()


@celery_app.task(name="process_screenshot")
def process_screenshot(evidence_id: str):
    """Process screenshot with VLM."""
    db = SessionLocal()
    try:
        evidence = db.query(EvidenceItem).filter(EvidenceItem.id == UUID(evidence_id)).first()
        if not evidence or not evidence.file_path:
            return
        
        if not os.path.exists(evidence.file_path):
            return
        
        # Analyze screenshot with VLM
        ml_service = MLService()
        prompt = "Describe what you see in this dashboard screenshot. Identify any errors, anomalies, or important metrics."
        
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            analysis = loop.run_until_complete(ml_service.analyze_image(evidence.file_path, prompt))
        finally:
            loop.close()
        
        # Update evidence with analysis
        if not evidence.content:
            evidence.content = analysis
        else:
            evidence.content = f"{evidence.content}\n\nVLM Analysis:\n{analysis}"
        
        db.commit()
        
        # Generate embedding
        rag_service = RAGService(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(rag_service.index_evidence(evidence))
        finally:
            loop.close()
        
        return {"status": "success", "analysis": analysis[:200] if analysis else ""}
    finally:
        db.close()

