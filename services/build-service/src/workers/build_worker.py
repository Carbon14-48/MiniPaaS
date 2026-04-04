import subprocess
from src.config import settings


def clone_repo(repo_url: str, branch: str, target_dir: str) -> str:
    subprocess.run(
        ["git", "clone", "--branch", branch, repo_url, target_dir],
        check=True,
    )
    return target_dir


def build_docker_image(context_dir: str, image_tag: str) -> str:
    subprocess.run(
        ["docker", "build", "-t", image_tag, context_dir],
        check=True,
    )
    return image_tag


def push_to_registry(image_tag: str) -> str:
    subprocess.run(
        ["docker", "push", image_tag],
        check=True,
    )
    return image_tag
