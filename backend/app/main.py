from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import incidents, evidence, hypotheses, runbooks, integrations
from app.config import settings

app = FastAPI(
    title="OpsLens API",
    description="Multimodal On-Call Copilot for Real Incidents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(incidents.router, prefix="/api/v1/incidents", tags=["incidents"])
app.include_router(evidence.router, prefix="/api/v1/evidence", tags=["evidence"])
app.include_router(hypotheses.router, prefix="/api/v1/hypotheses", tags=["hypotheses"])
app.include_router(runbooks.router, prefix="/api/v1/runbooks", tags=["runbooks"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])


@app.get("/")
async def root():
    return {
        "message": "OpsLens API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}

