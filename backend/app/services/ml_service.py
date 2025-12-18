"""ML service for interacting with Hugging Face Inference API."""
import httpx
from typing import Optional, List, Dict, Any
from app.config import settings
import base64
from pathlib import Path


class MLService:
    """Service for ML model interactions via Hugging Face Inference API."""
    
    def __init__(self):
        self.api_key = settings.HUGGINGFACE_API_KEY
        self.base_url = settings.HUGGINGFACE_API_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 512,
        temperature: float = 0.7
    ) -> str:
        """Generate text using LLM."""
        model = model or settings.LLM_MODEL
        url = f"{self.base_url}/models/{model}"
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "return_full_text": False
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            
            # Handle different response formats
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "")
            elif isinstance(result, dict):
                return result.get("generated_text", "")
            else:
                return str(result)
    
    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        model: Optional[str] = None
    ) -> str:
        """Analyze an image using VLM."""
        model = model or settings.VLM_MODEL
        url = f"{self.base_url}/models/{model}"
        
        # Read and encode image as base64
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            image_data = base64.b64encode(image_bytes).decode("utf-8")
        
        # Hugging Face Inference API format for vision-language models
        # Format: data:image/jpeg;base64,<base64_data> or just base64
        # For Qwen2-VL, we use the messages format
        payload = {
            "inputs": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "image": image_data
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            },
            "parameters": {
                "max_new_tokens": 512
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                
                # Handle loading state (model might be loading)
                if response.status_code == 503:
                    # Model is loading, wait and retry
                    import asyncio
                    await asyncio.sleep(10)
                    response = await client.post(url, json=payload, headers=self.headers)
                
                response.raise_for_status()
                result = response.json()
                
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    # Check for message format
                    if isinstance(result[0], dict):
                        if "generated_text" in result[0]:
                            return result[0]["generated_text"]
                        elif "message" in result[0]:
                            return result[0]["message"].get("content", "")
                    return str(result[0])
                elif isinstance(result, dict):
                    # Check for various response formats
                    if "generated_text" in result:
                        return result["generated_text"]
                    elif "message" in result:
                        return result["message"].get("content", "")
                    elif "text" in result:
                        return result["text"]
                    elif "output" in result:
                        return result["output"]
                    else:
                        # Return string representation
                        return str(result)
                else:
                    return str(result)
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
            print(f"VLM API Error: {error_msg}")
            raise Exception(f"VLM analysis failed: {error_msg}")
        except Exception as e:
            print(f"VLM Error: {str(e)}")
            raise Exception(f"VLM analysis failed: {str(e)}")
    
    async def generate_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings for texts."""
        model = model or settings.EMBEDDING_MODEL
        url = f"{self.base_url}/models/{model}"
        
        # BGE-M3 expects inputs as a list of strings
        payload = {
            "inputs": texts
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            
            # Handle different response formats
            if isinstance(result, list):
                # If it's a list of embeddings
                return result
            elif isinstance(result, dict) and "embeddings" in result:
                return result["embeddings"]
            else:
                # Try to extract embeddings from the response
                return result if isinstance(result, list) else [result]
    
    async def summarize_logs(self, logs: str) -> str:
        """Summarize log content."""
        prompt = f"""Summarize the following logs and identify key errors, warnings, and patterns:

{logs}

Summary:"""
        return await self.generate_text(prompt, max_tokens=256)
    
    async def generate_hypothesis(
        self,
        incident_title: str,
        evidence_summary: str
    ) -> Dict[str, Any]:
        """Generate a hypothesis about the root cause."""
        prompt = f"""Based on the following incident and evidence, generate a hypothesis about the root cause.

Incident: {incident_title}

Evidence:
{evidence_summary}

Provide a hypothesis in the following format:
Title: [Brief title]
Description: [Detailed explanation]
Confidence: [0.0-1.0]
Supporting Evidence: [List key evidence points]

Hypothesis:"""
        
        response = await self.generate_text(prompt, max_tokens=512)
        
        # Parse response (simplified - in production, use structured output)
        return {
            "title": incident_title.split(":")[0] if ":" in incident_title else f"Hypothesis for {incident_title}",
            "description": response,
            "confidence": 0.7  # Default, could be extracted from response
        }
    
    async def generate_timeline_summary(
        self,
        events: List[Dict[str, Any]]
    ) -> str:
        """Generate a human-readable timeline summary."""
        events_text = "\n".join([
            f"- {e.get('timestamp')}: {e.get('title')} ({e.get('event_type')})"
            for e in events
        ])
        
        prompt = f"""Create a clear, chronological timeline summary from these events:

{events_text}

Timeline Summary:"""
        
        return await self.generate_text(prompt, max_tokens=512)
    
    async def generate_postmortem(
        self,
        incident_title: str,
        timeline: str,
        hypotheses: List[str],
        resolution: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a postmortem draft."""
        hypotheses_text = "\n".join([f"- {h}" for h in hypotheses])
        
        prompt = f"""Write a postmortem for the following incident:

Title: {incident_title}

Timeline:
{timeline}

Hypotheses:
{hypotheses_text}

Resolution: {resolution or "Not yet resolved"}

Postmortem should include:
1. Summary
2. Root Cause Analysis
3. Contributing Factors
4. Impact
5. Resolution
6. Follow-up Actions

Postmortem:"""
        
        content = await self.generate_text(prompt, max_tokens=1024)
        
        return {
            "title": f"Postmortem: {incident_title}",
            "summary": content.split("\n\n")[0] if "\n\n" in content else content[:200],
            "root_cause": content,
            "contributing_factors": [],
            "impact": "To be determined",
            "resolution": resolution or "Pending",
            "follow_ups": []
        }

