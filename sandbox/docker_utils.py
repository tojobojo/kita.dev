import subprocess
import logging
import os

logger = logging.getLogger(__name__)


def ensure_sandbox_image(image_name: str = "kita-sandbox:latest"):
    """
    Checks if the docker image exists. If not, builds it from sandbox/Dockerfile.
    """
    # 1. Check existence
    try:
        subprocess.run(
            ["docker", "image", "inspect", image_name],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return  # Exists
    except subprocess.CalledProcessError:
        logger.info(f"Image {image_name} not found. Building...")

    # 2. Build
    sandbox_dir = os.path.dirname(os.path.abspath(__file__))
    dockerfile_path = os.path.join(sandbox_dir, "Dockerfile")

    if not os.path.exists(dockerfile_path):
        logger.error(
            f"Dockerfile not found at {dockerfile_path}. Cannot build sandbox."
        )
        raise FileNotFoundError(f"Dockerfile missing: {dockerfile_path}")

    try:
        subprocess.run(
            ["docker", "build", "-t", image_name, sandbox_dir],
            check=True,
            capture_output=True,
        )
        logger.info(f"Successfully built {image_name}")
    except subprocess.CalledProcessError as e:
        logger.error(
            f"Failed to build sandbox image: {e.stderr.decode() if e.stderr else 'Unknown error'}"
        )
        raise RuntimeError("Docker build failed")
