from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ml_service import MLService
from app.config import settings
import asyncio
import os
import tempfile

router = APIRouter()


@router.post("/test/vlm")
async def test_vlm(file: UploadFile = File(...)):
    """Test VLM with an uploaded image."""
    ml_service = MLService()
    
    if not ml_service.api_key:
        raise HTTPException(status_code=400, detail="Hugging Face API key not configured")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = tmp_file.name
    
    try:
        # Test different prompts
        prompts = [
            "Describe what you see in this image in detail.",
            "What errors or anomalies do you see?",
            "What are the key metrics and their values?",
            "Summarize the important information in this dashboard screenshot."
        ]
        
        results = {}
        for i, prompt in enumerate(prompts):
            try:
                analysis = await ml_service.analyze_image(tmp_path, prompt)
                results[f"prompt_{i+1}"] = {
                    "prompt": prompt,
                    "result": analysis,
                    "status": "success"
                }
            except Exception as e:
                results[f"prompt_{i+1}"] = {
                    "prompt": prompt,
                    "error": str(e),
                    "status": "error"
                }
        
        from app.config import settings
        
        return {
            "status": "completed",
            "model": settings.VLM_MODEL,
            "results": results,
            "file_info": {
                "filename": file.filename,
                "size": len(content),
                "content_type": file.content_type
            }
        }
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/test/vlm/status")
async def test_vlm_status():
    """Check if VLM is configured and ready."""
    from app.config import settings
    ml_service = MLService()
    
    return {
        "api_key_configured": bool(ml_service.api_key),
        "model": settings.VLM_MODEL,
        "api_url": ml_service.base_url,
        "status": "ready" if ml_service.api_key else "not_configured"
    }

