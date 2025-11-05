import os
from enum import Enum
from typing import Optional

import yaml
from pydantic import BaseModel, Field, field_validator

from hive_cli.utils import logger


class PlatformType(str, Enum):
    K8S = "k8s"
    ON_PREM = "on-prem"


class ResourceConfig(BaseModel):
    cpu: str = Field(
        default="1",
        description="The CPU resource request for the sandbox. Default to '1'.",
    )
    memory: str = Field(
        default="2Gi", description="The memory resource limit for the sandbox. Default to '2Gi'."
    )
    accelerators: Optional[str] = Field(
        default=None,
        description="The accelerator resource limit for the sandbox, e.g., 'a100-80gb:8'.",
    )
    shmsize: Optional[str] = Field(
        default=None, description="The size of /dev/shm for the sandbox container, e.g., '1Gi'."
    )
    extended_resources: Optional[dict] = None


class EnvConfig(BaseModel):
    name: str
    value: str


class SandboxConfig(BaseModel):
    image: Optional[str] = Field(
        default=None,
        description="The Docker image to use for the sandbox. If set, it will skip the image building step.",
    )
    build_args: Optional[dict] = Field(
        default=None,
        description="Build arguments to pass to the Docker build process when building the sandbox image.",
    )
    build_secret: Optional[str] = Field(
        default=None,
        description="The Docker build secret to use when building the sandbox image. Make sure you update your Dockerfile as well.",
    )
    target_platforms: list[str] = Field(
        default_factory=lambda: ["linux/amd64", "linux/arm64"],
        description="Target platforms for the sandbox Docker image. Default to ['linux/amd64', 'linux/arm64'].",
    )
    replicas: int = 1
    timeout: int = 60
    resources: ResourceConfig = Field(
        default_factory=ResourceConfig,
        description="Resource configuration for the sandbox.",
    )
    envs: Optional[list[EnvConfig]] = None
    pre_processor: Optional[str] = Field(
        default=None,
        description="The pre-processing script to run before the experiment. Use the `/data` directory to load/store datasets.",
    )


class PromptConfig(BaseModel):
    enable_evolution: bool = False


class RepoConfig(BaseModel):
    url: str
    branch: str = Field(
        default="main",
        description="The branch to use for the experiment. Default to 'main'.",
    )
    evaluation_script: str = Field(
        default="evaluator.py",
        description="The evaluation script to run for the experiment. Default to 'evaluator.py'.",
    )
    evolve_files_and_ranges: str = Field(
        description="Files to evolve, support line ranges like `file.py`, `file.py:1-10`, `file.py:1-10&21-30`."
    )
    include_files_and_ranges: str = Field(
        default="",
        description="Additional files to include in the prompt and their ranges, e.g. `file.py`, `file.py:1-10`, `file.py:1-10&21-30`.",
    )

    @field_validator("url")
    def url_should_not_be_git(cls, v):
        if v.startswith("git@"):
            raise ValueError("Only HTTPS URLs are allowed; git@ SSH URLs are not supported.")
        return v


class GCPConfig(BaseModel):
    enabled: bool = False
    spot: bool = False
    project_id: str = Field(
        description="The GCP project ID to use for the experiment.",
    )
    artifact_registry: str | None = Field(
        default=None,
        description="The GCP artifact registry to use for the experiment. If not set, will use the default GCP registry.",
    )


class AWSConfig(BaseModel):
    enabled: bool = False
    spot: bool = False
    artifact_registry: str | None = Field(
        default=None,
        description="The AWS artifact registry to use for the experiment. If not set, will use the default AWS ECR registry.",
    )


class ProviderConfig(BaseModel):
    gcp: Optional[GCPConfig] = None
    aws: Optional[AWSConfig] = None


class HiveConfig(BaseModel):
    project_name: str = Field(
        description="The name of the project. Must be all lowercase.",
    )

    token_path: str = Field(
        default=os.path.expandvars("$HOME/.kube/config"),
        description="Path to the auth token file, default to ~/.kube/config",
    )

    coordinator_config_name: str = Field(
        default="default-coordinator-config",
        description="The name of the coordinator config to use for the experiment. Default to 'default-coordinator-config'.",
    )

    platform: PlatformType = PlatformType.K8S

    repo: RepoConfig
    sandbox: SandboxConfig
    prompt: Optional[PromptConfig] = None
    # vendor configuration
    provider: ProviderConfig

    log_level: str = Field(
        default="INFO",
        enumerated=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        description="The logging level to use for the experiment. Default to 'INFO'.",
    )

    @field_validator("project_name")
    def must_be_lowercase(cls, v):
        if not v.islower():
            raise ValueError("project_name must be all lowercase")
        return v

    def model_post_init(self, __context):
        if (
            self.provider.gcp
            and self.provider.gcp.enabled
            and not self.provider.gcp.artifact_registry
        ):
            self.provider.gcp.artifact_registry = (
                f"gcr.io/{self.provider.gcp.project_id}/{self.project_name}"
            )

        if (
            self.provider.aws
            and self.provider.aws.enabled
            and not self.provider.aws.artifact_registry
        ):
            self.provider.aws.artifact_registry = (
                f"621302123805.dkr.ecr.eu-north-1.amazonaws.com/hiverge/{self.project_name}"
            )


def load_config(file_path: str) -> HiveConfig:
    """Load configuration from a YAML file."""
    with open(file_path, "r") as file:
        config_data = yaml.safe_load(file)
    config = HiveConfig(**config_data)

    # set the logging level.
    logger.set_log_level(config.log_level)
    return config
