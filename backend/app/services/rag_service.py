"""RAG service for semantic search over runbooks and postmortems."""
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.models import Runbook, Postmortem, EvidenceItem
from app.services.ml_service import MLService


class RAGService:
    """Service for Retrieval-Augmented Generation."""
    
    def __init__(self, db: Session):
        self.db = db
        self.ml_service = MLService()
    
    async def index_runbook(self, runbook_id: str):
        """Generate and store embedding for a runbook."""
        runbook = self.db.query(Runbook).filter(Runbook.id == runbook_id).first()
        if not runbook:
            return
        
        # Generate embedding
        text_to_embed = f"{runbook.title}\n{runbook.description or ''}\n{runbook.content}"
        embeddings = await self.ml_service.generate_embeddings([text_to_embed])
        
        if embeddings and len(embeddings) > 0:
            runbook.embedding = embeddings[0]
            self.db.commit()
    
    async def search_runbooks(
        self,
        query: str,
        service: Optional[str] = None,
        limit: int = 10
    ) -> List[Runbook]:
        """Search runbooks using semantic similarity."""
        # Generate query embedding
        embeddings = await self.ml_service.generate_embeddings([query])
        if not embeddings or len(embeddings) == 0:
            return []
        
        query_embedding = embeddings[0]
        
        # Build query
        sql_query = self.db.query(Runbook).filter(
            Runbook.embedding.isnot(None)
        )
        
        if service:
            sql_query = sql_query.filter(Runbook.service == service)
        
        # Use cosine similarity (pgvector)
        sql_query = sql_query.order_by(
            Runbook.embedding.cosine_distance(query_embedding)
        ).limit(limit)
        
        return sql_query.all()
    
    async def search_postmortems(
        self,
        query: str,
        limit: int = 10
    ) -> List[Postmortem]:
        """Search postmortems using semantic similarity."""
        # For postmortems, we'd need to add embedding column
        # For now, return text-based search
        return self.db.query(Postmortem).filter(
            Postmortem.title.ilike(f"%{query}%")
        ).limit(limit).all()
    
    async def get_relevant_runbooks_for_incident(
        self,
        incident_description: str,
        service: Optional[str] = None,
        limit: int = 5
    ) -> List[Runbook]:
        """Get relevant runbooks for an incident."""
        return await self.search_runbooks(incident_description, service=service, limit=limit)
    
    async def index_evidence(self, evidence: EvidenceItem):
        """Generate and store embedding for an evidence item."""
        if not evidence.content:
            return
        
        # Generate embedding
        embeddings = await self.ml_service.generate_embeddings([evidence.content])
        
        if embeddings and len(embeddings) > 0:
            evidence.embedding = embeddings[0]
            self.db.commit()

