"""PagerDuty integration for fetching incidents and alerts."""
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.config import settings


class PagerDutyIntegration:
    """Integration with PagerDuty API."""
    
    def __init__(self):
        self.api_key = settings.PAGERDUTY_API_KEY
        self.email = settings.PAGERDUTY_EMAIL
        self.base_url = "https://api.pagerduty.com"
        self.headers = {
            "Authorization": f"Token token={self.api_key}",
            "Accept": "application/vnd.pagerduty+json;version=2",
            "From": self.email or ""
        }
    
    async def get_incidents(
        self,
        statuses: List[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get incidents from PagerDuty."""
        if not self.api_key:
            return []
        
        statuses = statuses or ["triggered", "acknowledged"]
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        url = f"{self.base_url}/incidents"
        params = {
            "statuses[]": statuses,
            "since": since,
            "limit": 25
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("incidents", [])
        except Exception as e:
            print(f"Error fetching PagerDuty incidents: {e}")
            return []
    
    async def get_incident_details(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific incident."""
        if not self.api_key:
            return None
        
        url = f"{self.base_url}/incidents/{incident_id}"
        params = {
            "include[]": ["services", "assignments", "log_entries"]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                return response.json().get("incident")
        except Exception as e:
            print(f"Error fetching incident details: {e}")
            return None
    
    async def get_alerts(
        self,
        incident_id: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get alerts from PagerDuty."""
        if not self.api_key:
            return []
        
        since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        
        if incident_id:
            url = f"{self.base_url}/incidents/{incident_id}/alerts"
        else:
            url = f"{self.base_url}/incidents"
            # Filter by time
            params = {"since": since}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if incident_id:
                    response = await client.get(url, headers=self.headers)
                else:
                    response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                if "alerts" in data:
                    return data["alerts"]
                elif "incidents" in data:
                    # Extract alerts from incidents
                    alerts = []
                    for incident in data["incidents"]:
                        alerts.extend(incident.get("alerts", []))
                    return alerts
                return []
        except Exception as e:
            print(f"Error fetching alerts: {e}")
            return []

