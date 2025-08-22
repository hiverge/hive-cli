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
        context,
    ]
    if push:
        cmd.append("--push")

    if build_args:
        for key, value in build_args.items():
            cmd.extend(["--build-arg", f"{key}={value}"])

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
