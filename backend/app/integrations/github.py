"""GitHub integration for fetching PRs, diffs, and recent merges."""
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.config import settings


class GitHubIntegration:
    """Integration with GitHub API."""
    
    def __init__(self):
        self.api_key = settings.GITHUB_API_KEY
        self.org = settings.GITHUB_ORG
        self.base_url = "https://api.github.com"
        # Support both "token" and "Bearer" formats for GitHub API
        # Newer tokens use Bearer, older ones use token
        auth_header = f"Bearer {self.api_key}" if self.api_key and self.api_key.startswith("ghp_") else f"token {self.api_key}"
        self.headers = {
            "Authorization": auth_header,
            "Accept": "application/vnd.github.v3+json"
        }
    
    async def get_recent_merges(
        self,
        repo: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get recently merged PRs."""
        if not self.api_key:
            return []
        
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        # If repo is specified, search in that repo
        if repo:
            url = f"{self.base_url}/repos/{self.org}/{repo}/pulls"
            params = {
                "state": "closed",
                "sort": "updated",
                "direction": "desc",
                "per_page": 10
            }
        else:
            # Try to get user's repos first, then get PRs from them
            try:
                # Get user repos
                repos_url = f"{self.base_url}/user/repos"  # Use /user/repos to get authenticated user's repos
                async with httpx.AsyncClient(timeout=30.0) as client:
                    repos_response = await client.get(repos_url, headers=self.headers, params={"per_page": 10, "sort": "updated"})
                    if repos_response.status_code == 200:
                        repos = repos_response.json()
                        all_merges = []
                        # Get PRs from each repo
                        for repo_data in repos[:5]:  # Limit to 5 most recent repos
                            repo_name = repo_data["name"]
                            repo_owner = repo_data["owner"]["login"]
                            prs_url = f"{self.base_url}/repos/{repo_owner}/{repo_name}/pulls"
                            prs_params = {
                                "state": "closed",
                                "sort": "updated",
                                "direction": "desc",
                                "per_page": 5
                            }
                            prs_response = await client.get(prs_url, headers=self.headers, params=prs_params)
                            if prs_response.status_code == 200:
                                prs = prs_response.json()
                                # Filter for merged PRs only
                                for pr in prs:
                                    if pr.get("merged_at") and pr["merged_at"] >= since:
                                        pr["repository"] = {"full_name": f"{repo_owner}/{repo_name}"}
                                        all_merges.append(pr)
                        # Sort by merged_at and return
                        all_merges.sort(key=lambda x: x.get("merged_at", ""), reverse=True)
                        return all_merges[:10]
                    else:
                        # Fallback to search
                        url = f"{self.base_url}/search/issues"
                        params = {
                            "q": f"user:{self.org} is:pr is:merged merged:>={since}",
                            "sort": "updated",
                            "per_page": 10
                        }
                        response = await httpx.AsyncClient(timeout=30.0).get(url, headers=self.headers, params=params)
                        response.raise_for_status()
                        data = response.json()
                        return data.get("items", [])
            except Exception as e:
                print(f"Error in get_recent_merges: {e}")
                # Fallback to search
                url = f"{self.base_url}/search/issues"
                params = {
                    "q": f"user:{self.org} is:pr is:merged merged:>={since}",
                    "sort": "updated",
                    "per_page": 10
                }
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.get(url, headers=self.headers, params=params)
                        response.raise_for_status()
                        data = response.json()
                        return data.get("items", [])
                except:
                    return []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                if "items" in data:
                    return data["items"]
                # Filter for merged PRs only if we got a list
                if isinstance(data, list):
                    return [pr for pr in data if pr.get("merged_at")]
                return []
        except Exception as e:
            print(f"Error fetching GitHub merges: {e}")
            return []
    
    async def get_pr_details(self, repo: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """Get details of a specific PR."""
        if not self.api_key:
            return None
        
        url = f"{self.base_url}/repos/{self.org}/{repo}/pulls/{pr_number}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching PR details: {e}")
            return None
    
    async def get_pr_diff(self, repo: str, pr_number: int) -> Optional[str]:
        """Get the diff for a PR."""
        if not self.api_key:
            return None
        
        url = f"{self.base_url}/repos/{self.org}/{repo}/pulls/{pr_number}"
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers={**self.headers, "Accept": "application/vnd.github.v3.diff"}
                )
                response.raise_for_status()
                return response.text
        except Exception as e:
            print(f"Error fetching PR diff: {e}")
            return None
    
    async def get_recent_commits(
        self,
        repo: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get recent commits in a repository."""
        if not self.api_key:
            return []
        
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        url = f"{self.base_url}/repos/{self.org}/{repo}/commits"
        params = {
            "since": since,
            "per_page": 20
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching commits: {e}")
            return []

