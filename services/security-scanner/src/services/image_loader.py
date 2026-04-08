import docker
from docker.models.images import Image
import tempfile
import shutil
import os
from typing import Generator

from src.config import settings


class ImageLoader:
    """Handles loading and extracting Docker images for scanning."""

    def __init__(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
        except docker.errors.DockerException as e:
            raise RuntimeError(f"Cannot connect to Docker daemon: {e}")

    def get_image(self, image_tag: str) -> Image:
        """Get a Docker image by tag."""
        try:
            return self.client.images.get(image_tag)
        except docker.errors.NotFound:
            raise FileNotFoundError(f"Image not found: {image_tag}")
        except docker.errors.APIError as e:
            raise RuntimeError(f"Docker API error getting image {image_tag}: {e}")

    def get_base_image(self, image_tag: str) -> str:
        """Extract the FROM line / base image from an image's history."""
        try:
            img = self.get_image(image_tag)
            # Inspect the image to get the full config
            info = self.client.api.inspect_image(image_tag)
            config = info.get("Config", {})
            # Try to get base image from the image's parent chain
            parent_id = info.get("Parent", "")
            if not parent_id:
                # Top-level image — check if it has a scratch parent
                return "scratch"
            # Walk parent chain to find the base image
            base = self._find_base_image(image_tag)
            return base
        except Exception as e:
            raise RuntimeError(f"Failed to get base image for {image_tag}: {e}")

    def _find_base_image(self, image_tag: str) -> str:
        """Walk parent chain to find the original base image."""
        seen = set()
        current = image_tag

        for _ in range(20):
            if current in seen:
                break
            seen.add(current)

            try:
                info = self.client.api.inspect_image(current)
                parent_id = info.get("Parent", "")

                if not parent_id:
                    # This is the base image
                    # Try to get the image name from the tags
                    image_info = self.client.api.inspect_image(current)
                    repo_tags = image_info.get("RepoTags", [])
                    if repo_tags:
                        # Find the shortest tag (usually the base image name)
                        return min(repo_tags, key=len)
                    # Fallback: try to get from architecture/config
                    config = image_info.get("config", {})
                    if "Labels" in config:
                        labels = config["Labels"] or {}
                        for key in ["maintainer", "org.opencontainers.image.title"]:
                            if key in labels:
                                return labels[key]
                    return current

                # Move to parent
                current = self._resolve_image_id(parent_id)
            except Exception:
                break

        return current

    def _resolve_image_id(self, image_id: str) -> str:
        """Resolve an image ID to a tag name if possible."""
        try:
            img = self.client.images.get(image_id)
            tags = img.tags
            if tags:
                return tags[0]
            return image_id[:12]
        except Exception:
            return image_id[:12]

    def extract_layers(self, image_tag: str, dest_dir: str) -> str:
        """
        Extract all image layers to a directory for scanning.
        Returns the path to the extracted content.
        """
        os.makedirs(dest_dir, exist_ok=True)

        try:
            # Use docker save to extract layers
            image = self.get_image(image_tag)
            image_data = self.client.api.get_image(image_tag)

            # Save to tar archive in temp
            tar_path = os.path.join(dest_dir, f"{image_tag.replace('/', '_').replace(':', '_')}.tar")
            with open(tar_path, "wb") as f:
                for chunk in image_data:
                    f.write(chunk)

            # Extract tar
            import tarfile
            with tarfile.open(tar_path, "r") as tar:
                tar.extractall(dest_dir)

            # Remove tar file
            os.remove(tar_path)

            return dest_dir
        except Exception as e:
            raise RuntimeError(f"Failed to extract layers from {image_tag}: {e}")

    def list_files(self, image_tag: str) -> list[str]:
        """List all files in an image."""
        try:
            container = self.client.containers.create(image_tag)
            try:
                stdout = container.get_archive("/")
                files = []
                # Read the tar stream
                import tarfile
                import io
                while True:
                    try:
                        chunk = next(stdout)
                    except StopIteration:
                        break
                    files.append(chunk.decode("utf-8", errors="ignore"))
                return files
            finally:
                container.remove(force=True)
        except Exception as e:
            raise RuntimeError(f"Failed to list files in {image_tag}: {e}")

    def close(self):
        """Close the Docker client."""
        if hasattr(self, "client"):
            self.client.close()


def get_image_loader() -> Generator[ImageLoader, None, None]:
    """Context manager for ImageLoader."""
    loader = ImageLoader()
    try:
        yield loader
    finally:
        loader.close()
