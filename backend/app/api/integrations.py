from fastapi import APIRouter, HTTPException
from app.integrations.github import GitHubIntegration
from app.integrations.pagerduty import PagerDutyIntegration
import asyncio

router = APIRouter()


@router.get("/test/github")
async def test_github():
    """Test GitHub integration."""
    github = GitHubIntegration()
    
    if not github.api_key:
        raise HTTPException(status_code=400, detail="GitHub API key not configured")
    
    try:
        # Test getting recent merges
        merges = await github.get_recent_merges(hours=24)
        
        return {
            "status": "success",
            "api_key_configured": True,
            "org": github.org,
            "recent_merges_count": len(merges),
            "sample_merge": merges[0] if merges else None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "api_key_configured": True
        }


@router.get("/test/pagerduty")
async def test_pagerduty():
    """Test PagerDuty integration."""
    pagerduty = PagerDutyIntegration()
    
    if not pagerduty.api_key:
        raise HTTPException(status_code=400, detail="PagerDuty API key not configured")
    
    try:
        # Test getting incidents
        incidents = await pagerduty.get_incidents(hours=24)
        
        return {
            "status": "success",
            "api_key_configured": True,
            "email": pagerduty.email,
            "incidents_count": len(incidents),
            "sample_incident": incidents[0] if incidents else None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "api_key_configured": True
        }


@router.get("/test/all")
async def test_all_integrations():
    """Test all integrations."""
    results = {}
    
    # Test GitHub
    try:
        github_result = await test_github()
        results["github"] = github_result
    except Exception as e:
        results["github"] = {"status": "error", "error": str(e)}
    
    # Test PagerDuty
    try:
        pagerduty_result = await test_pagerduty()
        results["pagerduty"] = pagerduty_result
    except Exception as e:
        results["pagerduty"] = {"status": "error", "error": str(e)}
    
    return results

