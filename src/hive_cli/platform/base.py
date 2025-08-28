import importlib.resources as pkg_resources
import os
import shutil
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

import hive_cli
from hive_cli.config import HiveConfig
from hive_cli.runtime.runtime import Runtime
from hive_cli.utils import git, image
from hive_cli.utils.logger import logger


class Platform(Runtime, ABC):
    @abstractmethod
    def create(self, config: HiveConfig):
        pass

    @abstractmethod
    def update(self, name: str, config: HiveConfig):
        pass

    @abstractmethod
    def delete(self, name: str):
        pass

    @abstractmethod
    def login(self, args):
        pass

    @abstractmethod
    def show_experiments(self, args):
        pass

    @abstractmethod
    def show_sandboxes(self, args):
        pass

    @abstractmethod
    def log(self, args):
        pass

    def __init__(self, exp_name: str | None, token_path: str = None):
        super().__init__(exp_name, token_path)

    # setup_environment function can be used to prepare the environment for the experiment,
    # shared logic for both K8s and OnPrem platforms.
    def setup_environment(self, config: HiveConfig) -> HiveConfig:
        """
        Set up the environment for the experiment.
        This includes building the Docker image and preparing any necessary resources.

        Args:
            config (HiveConfig): The configuration for the experiment.

        Returns:
            HiveConfig: The updated configuration with the image name set.
        """

        logger.info(f"Setting up environment for experiment '{self.experiment_name}'")
        logger.debug(f"The HiveConfig: {config}")

        # Here you can add more setup logic, like initializing Kubernetes resources
        # or configuring the environment based on the HiveConfig.
        with tempfile.TemporaryDirectory() as temp_dir:
            image_name = self.prepare_images(config, temp_dir, push=True)

            # Populate related fields to the config, only allow to update here.
            config.sandbox.image = image_name

        logger.debug(f"The updated HiveConfig: {config}")
        return config

    def prepare_images(self, config: HiveConfig, temp_dir: str, push: bool = False) -> str:
        """
        Build the Docker image for the experiment.
        If `push` is True, it will push the image to the registry.

        Args:
            config (HiveConfig): The configuration for the experiment.
            temp_dir (str): The temporary directory to use for building the image.
            push (bool): Whether to push the image to the registry.

        Returns:
            str: The name of the built image.
        """

        logger.debug(f"Preparing images for experiment '{self.experiment_name}' in {temp_dir}")

        with pkg_resources.path(hive_cli, "libs") as lib_path:
            shutil.copytree(
                lib_path,
                temp_dir,
                dirs_exist_ok=True,
            )

        dest = Path(temp_dir) / "repo"
        hash = git.clone_repo(config.repo.url, dest, config.repo.branch)
        logger.debug(
            f"Cloning repository {config.repo.url} to {dest}, the tree structure of the directory: {os.listdir('.')}, the tree structure of the {dest} directory: {os.listdir(dest)}"
        )

        if not (dest / "Dockerfile").exists():
            logger.debug(f"No Dockerfile found in {dest}, generating one.")
            # Generate Dockerfile for the experiment
            generate_dockerfile(dest)

        logger.debug(f"Building temporary repo image in {dest}")
        # build the repository image first
        image.build_image(
            image="temp-image:latest",
            context=dest,
            dockerfile=dest / "Dockerfile",
            # this is a temporary image, so we don't push it
            push=False,
        )

        if config.cloud_provider.gcp and config.cloud_provider.gcp.enabled:
            image_registry = config.cloud_provider.gcp.image_registry
        elif config.cloud_provider.aws and config.cloud_provider.aws.enabled:
            image_registry = config.cloud_provider.aws.image_registry
        else:
            raise ValueError("Unsupported cloud provider configuration. Please enable GCP or AWS.")

        # Use the git commit hash as the image tag to ensure uniqueness.
        image_name = f"{image_registry}:{hash[:7]}"

        logger.debug(f"Building sandbox image {image_name} in {temp_dir} with push={push}")
        # build the sandbox image
        image.build_image(
            image=image_name,
            context=temp_dir,
            dockerfile=f"{temp_dir}/Dockerfile",
            push=push,
        )

        logger.debug(
            f"Images {image_name} prepared for experiment '{self.experiment_name}' successfully."
        )
        return image_name


# copied from the original hiverge project.
def generate_dockerfile(dest: Path) -> None:
    """Create a Dockerfile inside `dest`."""
    lines = [
        "FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim",
        "",
        "RUN apt-get update && apt-get install --no-install-recommends -y \\",
        "cmake \\",
        "build-essential \\",
        "pkg-config \\",
        "&& rm -rf /var/lib/apt/lists/*",
        "",
        "WORKDIR /app",
        "",
        "# Install sandbox server dependencies",
    ]
    if (dest / "pyproject.toml").exists():
        lines.append("# Install repository dependencies from pyproject.toml")
        lines.append("COPY pyproject.toml .")
        lines.append("RUN uv pip install --system --requirement pyproject.toml")
    elif (dest / "requirements.txt").exists():
        lines.append("# Install repository dependencies from requirements.txt")
        lines.append("COPY requirements.txt .")
        lines.append("RUN uv pip install --system --requirement requirements.txt")

    lines.extend(
        [
            "",
            "# Copy server code and evaluation file",
            "COPY . repo",
        ]
    )
    (dest / "Dockerfile").write_text("\n".join(lines), encoding="utf-8")
