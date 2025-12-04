import logging
import subprocess

from hive_cli.utils.logger import logger


def build_image(
    image: str,
    platforms: str = "linux/amd64,linux/arm64",
    context: str = ".",
    dockerfile: str = "Dockerfile",
    push: bool = False,
    build_args: dict = None,
    build_secret: str = None,
):
    cmd = [
        "docker",
        "buildx",
        "build",
        "--platform",
        platforms,
        "--file",
        dockerfile,
        "--tag",
        image,
        "--load",
    ]
    if push:
        cmd.append("--push")

    if build_args:
        for key, value in build_args.items():
            cmd.extend(["--build-arg", f"{key}={value}"])

    if build_secret:
        cmd.extend(["--secret", f"id={build_secret},env={build_secret}"])

    cmd.append(context)
    print(f"Image build command: {' '.join(map(str, cmd))}")

    try:
        if logger.isEnabledFor(logging.DEBUG):
            capture_output = False
        else:
            capture_output = True

        subprocess.run(
            cmd,
            check=True,
            capture_output=capture_output,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print("Build STDERR:\n", e.stderr)
        raise


BUILD_TEMPLATE = """
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', '{}', '.']
    env:
      - 'DOCKER_BUILDKIT=1'
images:
  - '{}'
"""


def build_image_in_cloud(image: str, context: str = ".") -> None:
    """Build a Docker image in GC Build and push it to Container Registry."""
    # For now we use subprocess to call gcloud CLI because the Python SDK does
    # not support building a local directory.

    build_yaml = BUILD_TEMPLATE.format(image, image)
    build_yaml_path = f"{context}/cloudbuild.yaml"
    with open(build_yaml_path, "w", encoding="utf-8") as f:
        f.write(build_yaml)

    cmd = ["gcloud", "builds", "submit", "--config", build_yaml_path, "."]
    print(f"Cloud image build command: {' '.join(map(str, cmd))}")

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=context,
        )
    except subprocess.CalledProcessError as e:
        print("Build STDERR:\n", e.stderr)
        raise
