import httpx
from ..config import settings
from typing import Optional


async def get_user_repos(token: str, page: int = 1, per_page: int = 30) -> list[dict]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(
                f"{settings.GITHUB_API_URL}/user/repos",
                params={"page": page, "per_page": per_page, "sort": "updated"},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            if response.status_code == 200:
                repos = response.json()
                return [
                    {
                        "id": repo["id"],
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "description": repo.get("description"),
                        "private": repo["private"],
                        "html_url": repo["html_url"],
                        "default_branch": repo["default_branch"],
                        "updated_at": repo["updated_at"],
                        "language": repo.get("language")
                    }
                    for repo in repos
                ]
            elif response.status_code == 401:
                raise ValueError("GitHub token invalid or expired")
            else:
                raise RuntimeError(f"GitHub API error: {response.status_code}")
        except httpx.ConnectError:
            raise RuntimeError("GitHub API unreachable")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch repos: {str(e)}")


async def get_repo_branches(token: str, owner: str, repo: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(
                f"{settings.GITHUB_API_URL}/repos/{owner}/{repo}/branches",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            if response.status_code == 200:
                branches = response.json()
                return [
                    {
                        "name": branch["name"],
                        "commit_sha": branch["commit"]["sha"],
                        "protected": branch.get("protected", False)
                    }
                    for branch in branches
                ]
            elif response.status_code == 404:
                raise ValueError(f"Repository {owner}/{repo} not found")
            elif response.status_code == 401:
                raise ValueError("GitHub token invalid or expired")
            else:
                raise RuntimeError(f"GitHub API error: {response.status_code}")
        except httpx.ConnectError:
            raise RuntimeError("GitHub API unreachable")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch branches: {str(e)}")
