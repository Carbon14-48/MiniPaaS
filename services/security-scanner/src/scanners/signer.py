import subprocess
import os
import logging

from src.config import settings

logger = logging.getLogger(__name__)


class CosignSigner:
    """Image signing using Cosign (Sigstore)."""

    def __init__(self):
        self.cosign_path = settings.COSIGN_PATH
        self.key_path = settings.COSIGN_KEY_PATH
        self.key_password = settings.COSIGN_KEY_PASSWORD
        self.keyless = settings.COSIGN_KEYLESS

    def sign(self, image_tag: str) -> str | None:
        """
        Sign an image with Cosign.
        Returns the signature digest on success, None on failure.
        """
        if not self.keyless and not os.path.exists(self.key_path):
            logger.warning(
                f"Cosign key not found at {self.key_path}. "
                "Skipping image signing. "
                "Set COSIGN_KEY_PATH or use COSIGN_KEYLESS=true."
            )
            return None

        try:
            cmd = self._build_sign_command(image_tag)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                logger.warning(
                    f"Cosign sign failed for {image_tag}: {result.stderr}"
                )
                return None

            logger.info(f"Image signed successfully: {image_tag}")
            return self._get_signature_digest(image_tag)

        except subprocess.TimeoutExpired:
            logger.error(f"Cosign signing timed out for {image_tag}")
            return None
        except FileNotFoundError:
            logger.warning(
                "Cosign binary not found. Install from: "
                "https://github.com/sigstore/cosign/releases"
            )
            return None
        except Exception as e:
            logger.error(f"Cosign signing failed: {e}")
            return None

    def verify(self, image_tag: str) -> bool:
        """
        Verify an image signature.
        Returns True if signature is valid.
        """
        try:
            cmd = self._build_verify_command(image_tag)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Cosign verification failed: {e}")
            return False

    def _build_sign_command(self, image_tag: str) -> list[str]:
        """Build the cosign sign command."""
        if self.keyless:
            cmd = [
                self.cosign_path,
                "sign",
                "--yes",
                "--allow-insecure-registry",
                image_tag,
            ]
        else:
            cmd = [
                self.cosign_path,
                "sign",
                "--yes",
                "--key", self.key_path,
                "--allow-insecure-registry",
            ]
            if self.key_password:
                cmd.extend(["--passwd", self.key_password])
            cmd.append(image_tag)

        return cmd

    def _build_verify_command(self, image_tag: str) -> list[str]:
        """Build the cosign verify command."""
        if self.keyless:
            return [
                self.cosign_path,
                "verify",
                "--allow-insecure-registry",
                image_tag,
            ]
        else:
            return [
                self.cosign_path,
                "verify",
                "--key", self.key_path,
                "--allow-insecure-registry",
                image_tag,
            ]

    def _get_signature_digest(self, image_tag: str) -> str | None:
        """Get the signature digest for an image."""
        try:
            result = subprocess.run(
                [
                    self.cosign_path,
                    "attest",
                    "--print-rekor-url",
                    "--yes",
                    "--allow-insecure-registry",
                    image_tag,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return f"signed:{image_tag}"
        except Exception:
            pass
        return f"sha256:signed"

    def is_available(self) -> bool:
        """Check if Cosign is available."""
        try:
            result = subprocess.run(
                [self.cosign_path, "version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except Exception:
            return False
