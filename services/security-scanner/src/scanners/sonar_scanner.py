import requests
from src.config import settings


def run_code_analysis(project_key: str, project_dir: str) -> dict:
    response = requests.post(
        f"{settings.SONARQUBE_URL}/api/qualitygates/project_status",
        params={"projectKey": project_key},
    )
    response.raise_for_status()
    return response.json()
