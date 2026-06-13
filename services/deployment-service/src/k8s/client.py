import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from src.config import settings

logger = logging.getLogger(__name__)

NAMESPACE = "cloudoku"


def load_kube_config():
    try:
        config.load_incluster_config()
        logger.info("Using in-cluster kube config")
    except config.ConfigException:
        config.load_kube_config(config_file=settings.KUBECONFIG_PATH)
        logger.info(f"Loaded kube config from {settings.KUBECONFIG_PATH}")


def create_deployment(name: str, image: str, replicas: int, env_vars: dict) -> dict:
    load_kube_config()
    apps_v1 = client.AppsV1Api()
    container = client.V1Container(
        name=name,
        image=image,
        env=[client.V1EnvVar(name=k, value=str(v)) for k, v in env_vars.items()],
        ports=[client.V1ContainerPort(container_port=80)],
    )
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": name}),
        spec=client.V1PodSpec(containers=[container]),
    )
    spec = client.V1DeploymentSpec(
        replicas=replicas,
        selector=client.V1LabelSelector(match_labels={"app": name}),
        template=template,
    )
    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=name, namespace=NAMESPACE),
        spec=spec,
    )
    try:
        apps_v1.create_namespaced_deployment(namespace=NAMESPACE, body=deployment)
        logger.info(f"Created deployment {name} in namespace {NAMESPACE}")
        return {"name": name, "image": image, "replicas": replicas, "status": "created"}
    except ApiException as e:
        if e.status == 409:
            body = {"spec": {"replicas": replicas}}
            apps_v1.patch_namespaced_deployment(name=name, namespace=NAMESPACE, body=body)
            logger.info(f"Updated deployment {name} replicas to {replicas}")
            return {"name": name, "image": image, "replicas": replicas, "status": "updated"}
        logger.error(f"Failed to create deployment {name}: {e}")
        raise


def delete_deployment(name: str) -> dict:
    load_kube_config()
    apps_v1 = client.AppsV1Api()
    try:
        apps_v1.delete_namespaced_deployment(name=name, namespace=NAMESPACE)
        logger.info(f"Deleted deployment {name}")
        return {"name": name, "status": "deleted"}
    except ApiException as e:
        if e.status == 404:
            logger.warning(f"Deployment {name} not found")
            return {"name": name, "status": "not_found"}
        logger.error(f"Failed to delete deployment {name}: {e}")
        raise


def scale_deployment(name: str, replicas: int) -> dict:
    load_kube_config()
    apps_v1 = client.AppsV1Api()
    body = {"spec": {"replicas": replicas}}
    try:
        apps_v1.patch_namespaced_deployment(name=name, namespace=NAMESPACE, body=body)
        logger.info(f"Scaled deployment {name} to {replicas} replicas")
        return {"name": name, "replicas": replicas, "status": "scaled"}
    except ApiException as e:
        logger.error(f"Failed to scale deployment {name}: {e}")
        raise


def create_service(name: str, port: int) -> dict:
    load_kube_config()
    core_v1 = client.CoreV1Api()
    service = client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=client.V1ObjectMeta(name=name, namespace=NAMESPACE),
        spec=client.V1ServiceSpec(
            selector={"app": name},
            ports=[client.V1ServicePort(port=port, target_port=80)],
            type="ClusterIP",
        ),
    )
    try:
        core_v1.create_namespaced_service(namespace=NAMESPACE, body=service)
        logger.info(f"Created service {name} on port {port}")
        return {
            "name": name,
            "port": port,
            "url": f"https://{name}.{settings.CLOUDOKU_DOMAIN}",
        }
    except ApiException as e:
        if e.status == 409:
            logger.info(f"Service {name} already exists")
            return {
                "name": name,
                "port": port,
                "url": f"https://{name}.{settings.CLOUDOKU_DOMAIN}",
            }
        logger.error(f"Failed to create service {name}: {e}")
        raise
