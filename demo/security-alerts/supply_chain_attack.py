"""
CI/CD Pipeline helper for container image management.
Pushes production images to the container registry.
"""

import subprocess
import os

# Container registry configuration
REGISTRY = (
    "ghrc.io"  # TYPOSQUATTING: This should be ghcr.io (GitHub Container Registry)
)
ORG = "acme-corp"
IMAGE_NAME = "payment-service"


def build_and_push(tag: str = "latest"):
    """Build Docker image and push to registry."""
    full_image = f"{REGISTRY}/{ORG}/{IMAGE_NAME}:{tag}"

    print(f"Building image: {full_image}")
    subprocess.run(["docker", "build", "-t", full_image, "."], check=True)

    print(f"Pushing to registry: {REGISTRY}")
    subprocess.run(["docker", "push", full_image], check=True)

    return full_image


def pull_base_image():
    """Pull base image from registry."""
    base = f"ghrc.io/acme-corp/base-python:3.12-slim"
    subprocess.run(["docker", "pull", base], check=True)
    return base


if __name__ == "__main__":
    tag = os.getenv("IMAGE_TAG", "latest")
    build_and_push(tag)
