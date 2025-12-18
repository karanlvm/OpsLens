from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import incidents, evidence, hypotheses, runbooks, integrations, vlm_test, webhooks, auth
from app.auth.security import get_api_key
from app.config import settings
from fastapi import Depends
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
# Public endpoints (no auth required)
app.include_router(webhooks.router, prefix="/api/v1", tags=["webhooks"])
app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])

# Protected endpoints (API key required)
# Note: In development, auth is optional. Set ENABLE_AUTH=true to enforce.
ENABLE_AUTH = settings.ENABLE_AUTH

if ENABLE_AUTH:
    app.include_router(incidents.router, prefix="/api/v1/incidents", tags=["incidents"], dependencies=[Depends(get_api_key)])
    app.include_router(evidence.router, prefix="/api/v1/evidence", tags=["evidence"], dependencies=[Depends(get_api_key)])
    app.include_router(hypotheses.router, prefix="/api/v1/hypotheses", tags=["hypotheses"], dependencies=[Depends(get_api_key)])
    app.include_router(runbooks.router, prefix="/api/v1/runbooks", tags=["runbooks"], dependencies=[Depends(get_api_key)])
    app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"], dependencies=[Depends(get_api_key)])
    app.include_router(vlm_test.router, prefix="/api/v1", tags=["vlm-test"], dependencies=[Depends(get_api_key)])
else:
    # Development mode - no auth required
    app.include_router(incidents.router, prefix="/api/v1/incidents", tags=["incidents"])
    app.include_router(evidence.router, prefix="/api/v1/evidence", tags=["evidence"])
    app.include_router(hypotheses.router, prefix="/api/v1/hypotheses", tags=["hypotheses"])
    app.include_router(runbooks.router, prefix="/api/v1/runbooks", tags=["runbooks"])
    app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["integrations"])
    app.include_router(vlm_test.router, prefix="/api/v1", tags=["vlm-test"])


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

