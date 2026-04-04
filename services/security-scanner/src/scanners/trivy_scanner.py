import subprocess
import json
from src.config import settings


def scan_container_image(image_tag: str) -> dict:
    result = subprocess.run(
        ["trivy", "image", "--format", "json", image_tag],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return json.loads(result.stdout)
    return {"error": result.stderr, "exit_code": result.returncode}
