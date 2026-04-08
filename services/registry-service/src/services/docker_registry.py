"""
services/docker_registry.py
----------------------------
Logique Docker interne au registry-service.

Ce fichier contient TOUTES les opérations Docker :
  - Vérifier qu'une image existe localement
  - Tagger une image pour le registry local
  - Pusher vers registry:5000
  - Supprimer les images locales après push (nettoyage disque)
  - Supprimer une image du registry (via API V2)

IMPORTANT : Ce fichier n'appelle AUCUN autre microservice.
Il communique uniquement avec le daemon Docker via le SDK Python
et avec registry:5000 via l'API Docker Registry V2.
"""

import httpx
import docker
from docker.errors import ImageNotFound, APIError, DockerException
from fastapi import HTTPException, status
from src.config import settings


def get_docker_client():
    """
    Retourne un client Docker connecté au daemon local.
    Lève 503 si le daemon est injoignable.
    """
    try:
        client = docker.from_env()
        client.ping()
        return client
    except DockerException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Docker daemon injoignable — vérifier /var/run/docker.sock"
        )


def image_exists_locally(image_tag: str) -> bool:
    """
    Vérifie qu'une image existe sur le daemon Docker local.

    Le build-service crée l'image localement puis appelle /push.
    Si l'image n'existe pas, le build a échoué ou a déjà été nettoyé.

    Paramètre :
        image_tag : ex "user42/myapp:v1"

    Retourne :
        True si l'image existe, False sinon
    """
    client = get_docker_client()
    try:
        client.images.get(image_tag)
        return True
    except ImageNotFound:
        return False


def push_to_registry(image_tag: str) -> dict:
    """
    Taggue l'image pour le registry local, la push, puis nettoie.

    Étapes internes :
      1. Construit l'URL registry : registry:5000/user42/myapp:v1
      2. docker tag  user42/myapp:v1  registry:5000/user42/myapp:v1
      3. docker push registry:5000/user42/myapp:v1
      4. Extrait digest + size depuis les logs de push
      5. Supprime les deux versions locales (nettoyage disque)

    Paramètre :
        image_tag : tag original (ex: "user42/myapp:v1")

    Retourne :
        dict avec registry_url, digest, size_bytes

    Lève :
        HTTPException 404 si l'image n'existe pas localement
        HTTPException 503 si registry:5000 est injoignable
        HTTPException 500 pour toute autre erreur Docker
    """
    # Construit l'URL complète dans le registry
    registry_url = f"{settings.registry_host}/{image_tag}"

    # Vérifie que l'image existe localement avant de tenter quoi que ce soit
    if not image_exists_locally(image_tag):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Image '{image_tag}' introuvable sur le daemon Docker local. "
                f"Le build-service doit builder l'image avant d'appeler /push."
            )
        )

    client = get_docker_client()

    try:
        # Étape 1 : docker tag user42/myapp:v1  registry:5000/user42/myapp:v1
        image = client.images.get(image_tag)
        image.tag(registry_url)

    except APIError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur docker tag : {str(e)}"
        )

    # Étape 2 : docker push registry:5000/user42/myapp:v1
    digest = None
    size_bytes = None

    try:
        push_output = client.images.push(
            registry_url,
            stream=True,
            decode=True
        )

        for line in push_output:
            # Cherche le digest dans les logs de push
            # Format : {"aux": {"Digest": "sha256:abc...", "Size": 12345}}
            if "aux" in line:
                aux = line["aux"]
                digest = aux.get("Digest")
                size_bytes = aux.get("Size")

            # Détecte les erreurs de push
            if "error" in line:
                error_msg = line.get("error", "Erreur inconnue")

                # Erreur spécifique : registry injoignable
                if "connection refused" in error_msg.lower() or \
                   "no such host" in error_msg.lower():
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=(
                            f"Registry {settings.registry_host} injoignable. "
                            f"Vérifier que le container registry:2 tourne "
                            f"et que daemon.json contient insecure-registries."
                        )
                    )

                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Erreur docker push : {error_msg}"
                )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur inattendue lors du push : {str(e)}"
        )

    finally:
        # Étape 3 : nettoyage TOUJOURS exécuté même si push échoue partiellement
        # On supprime les images locales pour libérer l'espace disque
        _cleanup_local_images(client, image_tag, registry_url)

    return {
        "registry_url": registry_url,
        "digest": digest,
        "size_bytes": size_bytes,
    }


def _cleanup_local_images(client, image_tag: str, registry_url: str) -> None:
    """
    Supprime les images locales après push.
    Appelé dans le bloc finally — ne lève jamais d'exception.

    Après push, l'image est dans registry:5000.
    Le daemon local n'en a plus besoin — on libère l'espace disque.
    """
    for tag in [registry_url, image_tag]:
        try:
            client.images.remove(tag, force=True)
        except Exception:
            # On ignore les erreurs de nettoyage — l'image est déjà pushée
            pass


def delete_from_registry(registry_url: str) -> bool:
    """
    Supprime une image du registry local via l'API Docker Registry V2.

    L'API V2 du registry:2 permet de supprimer une image par son digest.
    Cette opération est irréversible côté registry.

    Note : Le registry:2 nécessite d'être configuré avec
    REGISTRY_STORAGE_DELETE_ENABLED=true pour autoriser les suppressions.

    Paramètre :
        registry_url : ex "registry:5000/user42/myapp:v1"

    Retourne :
        True si suppression réussie, False sinon
    """
    try:
        # Extrait "user42/myapp" et "v1" depuis l'URL
        # registry_url = "registry:5000/user42/myapp:v1"
        path = registry_url.replace(f"{settings.registry_host}/", "")
        if ":" in path:
            name, tag = path.rsplit(":", 1)
        else:
            name, tag = path, "latest"

        # Étape 1 : récupère le digest via l'API V2
        manifest_url = (
            f"{settings.registry_url}/v2/{name}/manifests/{tag}"
        )

        import httpx as _httpx
        headers = {
            "Accept": "application/vnd.docker.distribution.manifest.v2+json"
        }

        resp = _httpx.get(manifest_url, headers=headers, timeout=10.0)

        if resp.status_code == 404:
            return False

        resp.raise_for_status()
        digest = resp.headers.get("Docker-Content-Digest")

        if not digest:
            return False

        # Étape 2 : supprime via le digest
        delete_url = f"{settings.registry_url}/v2/{name}/manifests/{digest}"
        del_resp = _httpx.delete(delete_url, timeout=10.0)

        return del_resp.status_code in (200, 202)

    except Exception:
        return False
