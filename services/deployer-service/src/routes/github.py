from fastapi import APIRouter, Query
from typing import Optional
from pydantic import BaseModel

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
        raise ValueError("Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ValueError("Invalid Authorization header format")
    return parts[1]


@router.get("/", response_model=list[RepoResponse])
async def list_repos(
    authorization: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100)
):
    token = get_token_from_header(authorization)
    repos = await get_user_repos(token, page=page, per_page=per_page)
    return repos


@router.get("/{owner}/{repo}/branches", response_model=list[BranchResponse])
async def list_branches(
    authorization: str,
    owner: str,
    repo: str
):
    token = get_token_from_header(authorization)
    branches = await get_repo_branches(token, owner, repo)
    return branches
