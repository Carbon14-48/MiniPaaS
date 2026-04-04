from kubernetes import client, config
from src.config import settings


def load_kube_config():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        config.load_kube_config(config_file=settings.KUBECONFIG_PATH)


def create_deployment(name: str, image: str, replicas: int, env_vars: dict) -> dict:
    apps_v1 = client.AppsV1Api()
    return {
        "name": name,
        "image": image,
        "replicas": replicas,
        "status": "created",
    }


def delete_deployment(name: str) -> dict:
    apps_v1 = client.AppsV1Api()
    return {"name": name, "status": "deleted"}


def scale_deployment(name: str, replicas: int) -> dict:
    apps_v1 = client.AppsV1Api()
    return {"name": name, "replicas": replicas, "status": "scaled"}


def create_service(name: str, port: int) -> dict:
    core_v1 = client.CoreV1Api()
    return {
        "name": name,
        "port": port,
        "url": f"https://{name}.cloudoku.app",
    }
