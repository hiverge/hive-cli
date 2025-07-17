import shutil
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path

from hive_cli.config import HiveConfig
from hive_cli.runtime.runtime import Runtime
from hive_cli.utils import git
from hive_cli.utils.image import build_image
from hive_cli.utils.logger import logger


class Platform(Runtime, ABC):
    @abstractmethod
    def create(self, config: HiveConfig):
        pass

    @abstractmethod
    def delete(self, args):
        pass

    @abstractmethod
    def login(self, args):
        pass

    @abstractmethod
    def show_experiments(self, args):
        pass

    def __init__(self, name: str):
        super().__init__(name)

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
        with tempfile.TemporaryDirectory(dir="./tmp") as temp_dir:
            image_name = self.prepare_images(config, temp_dir, push=True)

            # Populate related fields to the config, only allow to update here.
            config.evaluator.image = image_name

        logger.debug(f"The updated HiveConfig: {config}")

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

        # TODO: refactor this part to use an image by default rather than build from the scratch.
        shutil.copytree(
            "./libraries",
            Path("./tmp") / temp_dir,
            dirs_exist_ok=True,
        )
        dest = Path(temp_dir) / "repo"

        logger.debug(f"Cloning repository {config.repo.url} to {dest}")
        git.clone_repo(config.repo.url, dest, config.repo.branch)

        if not (dest / "Dockerfile").exists():
            # Generate Dockerfile for the experiment
            generate_dockerfile(dest)

        logger.debug(f"Building temporary repo image in {dest}")
        # build the repository image first
        build_image(
            image="repo-image:latest",
            platforms="linux/amd64",
            context=dest,
            dockerfile=dest / "Dockerfile",
            # this is a temporary image, so we don't push it
            push=False,
        )

        # TODO: what if we don't use GCP?
        image_name = f"gcr.io/{config.gcp.project_id}/{self.experiment_name}"

        logger.debug(f"Building evaluator image {image_name} in {temp_dir} with push={push}")
        # build the evaluator image
        build_image(
            image=image_name,
            platforms="linux/amd64",
            context=temp_dir,
            dockerfile=f"{temp_dir}/Dockerfile",
            push=push,
        )

        logger.debug(
            f"Images {image_name} prepared for experiment '{self.experiment_name}' successfully."
        )
        return image_name


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
