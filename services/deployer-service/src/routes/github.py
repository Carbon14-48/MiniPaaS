from fastapi import APIRouter, Query, Header, HTTPException
from typing import Optional
from pydantic import BaseModel
import httpx

from ..config import settings
from ..services.github_client import get_user_repos, get_repo_branches

router = APIRouter(prefix="/repos", tags=["github"])


class RepoResponse(BaseModel):
    id: int
    name: str
    full_name: str
    description: Optional[str]
    private: bool
    html_url: str
    default_branch: str
    updated_at: str
    language: Optional[str]


class BranchResponse(BaseModel):
    name: str
    commit_sha: str
    protected: bool


def get_token_from_header(authorization: str) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    return authorization[7:].strip()


async def get_github_token(minipaas_token: str) -> str:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{settings.AUTH_SERVICE_URL}/auth/github-token",
                headers={"Authorization": f"Bearer {minipaas_token}"}
            )
            if response.status_code == 200:
                data = response.json()
                github_token = data.get("github_token")
                if not github_token:
                    raise HTTPException(status_code=401, detail="No GitHub token found. Please login with GitHub OAuth first.")
                return github_token
            else:
                raise HTTPException(status_code=response.status_code, detail=f"Failed to get GitHub token")
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Auth service unreachable")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get GitHub token: {str(e)}")


@router.get("/", response_model=list[RepoResponse])
async def list_repos(
    authorization: str = Header(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100)
):
    token = get_token_from_header(authorization)
    github_token = await get_github_token(token)
    repos = await get_user_repos(github_token, page=page, per_page=per_page)
    return repos


@router.get("/{owner}/{repo}/branches", response_model=list[BranchResponse])
async def list_branches(
    authorization: str = Header(None),
    owner: str = None,
    repo: str = None
):
    token = get_token_from_header(authorization)
    github_token = await get_github_token(token)
    branches = await get_repo_branches(github_token, owner, repo)
    return branches
