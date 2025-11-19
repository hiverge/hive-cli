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
        super().__init__(exp_name)

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
        image_name = (
            self.prepare_images(config, push=True)
            if not config.sandbox.image
            else config.sandbox.image
        )

        # Populate related fields to the config, only allow to update here.
        config.sandbox.image = image_name

        logger.debug(f"The updated HiveConfig: {config}")
        return config

    def prepare_images(self, config: HiveConfig, push: bool = False) -> str:
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

        with tempfile.TemporaryDirectory() as temp_repo_dir:
            logger.debug(
                f"Preparing repo image for experiment '{self.experiment_name}' in {temp_repo_dir}"
            )

            dest = Path(temp_repo_dir) / "repo"
            hash = git.get_codebase(config.repo.source, str(dest), config.repo.branch)
            logger.debug(
                f"Cloning repository {config.repo.source} to {dest}, the tree structure of the directory: {os.listdir('.')}, the tree structure of the {dest} directory: {os.listdir(dest)}"
            )

            if not (dest / "Dockerfile").exists():
                logger.debug(f"No Dockerfile found in {dest}, generating one.")
                # Generate Dockerfile for the experiment
                generate_dockerfile(dest)

            # Add ".git" to .dockerignore to improve caching
            generate_dockerignore(dest)

            logger.debug(f"Building temporary repo image in {dest}")
            # build the repository image first
            image.build_image(
                image="temp-image:latest",
                context=dest,
                dockerfile=dest / "Dockerfile",
                platforms=",".join(config.sandbox.target_platforms),
                # this is a temporary image, so we don't push it
                push=False,
                build_args=config.sandbox.build_args,
                build_secret=config.sandbox.build_secret,
            )

        with tempfile.TemporaryDirectory() as temp_sandbox_dir:
            logger.debug(
                f"Preparing sandbox image for experiment '{self.experiment_name}' in {temp_sandbox_dir}"
            )

            with pkg_resources.path(hive_cli, "libs") as lib_path:
                shutil.copytree(
                    lib_path,
                    temp_sandbox_dir,
                    dirs_exist_ok=True,
                )

            if config.provider.gcp and config.provider.gcp.enabled:
                image_registry = config.provider.gcp.artifact_registry
            elif config.provider.aws and config.provider.aws.enabled:
                image_registry = config.provider.aws.artifact_registry
            else:
                raise ValueError(
                    "Unsupported cloud provider configuration. Please enable GCP or AWS."
                )

            # Use the git commit hash as the image tag to ensure uniqueness.
            image_name = f"{image_registry}:{hash[:7]}"

            logger.debug(
                f"Building sandbox image {image_name} in {temp_sandbox_dir} with push={push}"
            )
            # build the sandbox image
            image.build_image(
                image=image_name,
                context=temp_sandbox_dir,
                dockerfile=f"{temp_sandbox_dir}/Dockerfile",
                platforms=",".join(config.sandbox.target_platforms),
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
        lines.append(
            "RUN uv pip install --system --break-system-packages --requirement pyproject.toml"
        )
    elif (dest / "requirements.txt").exists():
        lines.append("# Install repository dependencies from requirements.txt")
        lines.append("COPY requirements.txt .")
        lines.append(
            "RUN uv pip install --system --break-system-packages --requirement requirements.txt"
        )

    lines.extend(
        [
            "",
            "# Copy server code and evaluation file",
            "COPY . repo",
        ]
    )
    (dest / "Dockerfile").write_text("\n".join(lines), encoding="utf-8")


def generate_dockerignore(dest: Path) -> None:
    """Create a .dockerignore file inside `dest`."""
    if (dest / ".dockerignore").exists():
        # If there's a .dockerignore already, append ".git" to it.
        with open(dest / ".dockerignore", "a", encoding="utf-8") as f:
            f.write("\n.git\n")
    else:
        # Otherwise, create a new .dockerignore file.
        (dest / ".dockerignore").write_text(".git", encoding="utf-8")
