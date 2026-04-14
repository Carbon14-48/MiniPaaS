import docker
from docker.errors import DockerException, NotFound
from typing import Optional
from ..config import settings
import logging

logger = logging.getLogger(__name__)


class DockerRunner:
    def __init__(self):
        self._client = None

    @property
    def client(self) -> docker.DockerClient:
        if self._client is None:
            self._client = docker.from_env()
            self._client.ping()
        return self._client

    def _find_available_port(self) -> int:
        used_ports = set()
        for container in self.client.containers.list(all=True):
            try:
                ports = container.attrs.get('NetworkSettings', {}).get('Ports', {})
                for port_bindings in ports.values():
                    if port_bindings:
                        for binding in port_bindings:
                            if binding.get('HostPort'):
                                used_ports.add(int(binding['HostPort']))
            except Exception:
                pass
        
        for port in range(settings.HOST_PORT_RANGE_START, settings.HOST_PORT_RANGE_END):
            if port not in used_ports:
                return port
        raise RuntimeError("No available ports in range")

    def run_container(
        self,
        image_tag: str,
        app_name: str,
        user_id: int,
        env_vars: Optional[dict] = None,
        port: Optional[int] = None
    ) -> dict:
        container_name = f"minipaas-{user_id}-{app_name}"
        
        try:
            existing = self.client.containers.get(container_name)
            logger.info(f"Removing existing container {container_name}")
            existing.stop(timeout=5)
            existing.remove()
        except NotFound:
            pass
        except DockerException as e:
            logger.warning(f"Could not remove existing container: {e}")

        host_port = port or self._find_available_port()
        
        env = []
        if env_vars:
            for key, value in env_vars.items():
                env.append(f"{key}={value}")
        
        registry_url = "localhost:5000"
        registry_image = f"{registry_url}/{image_tag}"
        
        try:
            self.client.images.get(image_tag)
            logger.info(f"Image {image_tag} found locally")
            run_image = image_tag
        except NotFound:
            try:
                logger.info(f"Image {image_tag} not found locally, pulling from registry {registry_image}")
                self.client.images.pull(registry_image)
                run_image = registry_image
            except DockerException as e:
                logger.warning(f"Could not pull {registry_image}, trying {image_tag}")
                raise ValueError(f"Image {image_tag} not found. Registry pull failed: {e}")

        container = self.client.containers.run(
            image=run_image,
            name=container_name,
            detach=True,
            ports={
                "8000/tcp": host_port
            },
            environment=env if env else None,
            restart_policy={"Name": "unless-stopped"},
            labels={
                "minipaas": "true",
                "user_id": str(user_id),
                "app_name": app_name
            }
        )

        container.reload()

        return {
            "container_id": container.id,
            "container_short_id": container.short_id,
            "host_port": host_port,
            "container_port": 8000,
            "status": container.status,
            "container_url": f"http://localhost:{host_port}"
        }

    def stop_container(self, container_id: str) -> bool:
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=10)
            return True
        except NotFound:
            logger.warning(f"Container {container_id} not found")
            return False
        except DockerException as e:
            logger.error(f"Error stopping container {container_id}: {e}")
            raise

    def remove_container(self, container_id: str) -> bool:
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=5)
            container.remove()
            return True
        except NotFound:
            logger.warning(f"Container {container_id} not found")
            return False
        except DockerException as e:
            logger.error(f"Error removing container {container_id}: {e}")
            raise

    def get_container_status(self, container_id: str) -> dict:
        try:
            container = self.client.containers.get(container_id)
            container.reload()
            return {
                "container_id": container.id,
                "short_id": container.short_id,
                "status": container.status,
                "container_url": None,
                "created": container.attrs.get('Created'),
                "ports": container.ports
            }
        except NotFound:
            return {"status": "not_found", "container_id": container_id}
        except DockerException as e:
            return {"status": "error", "error": str(e)}

    def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, timestamps=True).decode('utf-8')
            return logs
        except NotFound:
            return f"Container {container_id} not found"
        except DockerException as e:
            return f"Error fetching logs: {str(e)}"

    def list_user_containers(self, user_id: int) -> list[dict]:
        containers = []
        for container in self.client.containers.list(all=True):
            labels = container.labels or {}
            if labels.get('minipaas') == 'true' and labels.get('user_id') == str(user_id):
                container.reload()
                containers.append({
                    "container_id": container.id,
                    "short_id": container.short_id,
                    "app_name": labels.get('app_name', 'unknown'),
                    "status": container.status,
                    "ports": container.ports
                })
        return containers

    def pull_image(self, image_tag: str) -> bool:
        try:
            logger.info(f"Pulling image {image_tag}")
            self.client.images.pull(image_tag)
            return True
        except DockerException as e:
            logger.error(f"Error pulling image {image_tag}: {e}")
            raise


docker_runner = DockerRunner()
