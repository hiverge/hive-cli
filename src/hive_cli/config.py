import os
from enum import Enum
from typing import Optional

import yaml
from pydantic import BaseModel, Field, field_validator

from hive_cli.utils import logger


class PlatformType(str, Enum):
    K8S = "k8s"
    # ON_PREM = "on-prem"


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


class PortConfig(BaseModel):
    port: int = Field(
        description="The port number inside the container.",
    )
    protocol: Optional[str] = Field(
        default="TCP",
        description="The protocol for the port. Default to 'TCP'.",
    )


class ServiceConfig(BaseModel):
    name: str
    image: str
    ports: Optional[list[PortConfig]] = None
    envs: Optional[list[EnvConfig]] = None
    command: Optional[list[str]] = None
    args: Optional[list[str]] = None
    resources: ResourceConfig = Field(
        default_factory=ResourceConfig,
        description="Resource configuration for the service.",
    )


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
    timeout: int = 60
    resources: ResourceConfig = Field(
        default_factory=ResourceConfig,
        description="Resource configuration for the sandbox.",
    )
    envs: Optional[list[EnvConfig]] = Field(
        default=None,
        description="Environment variables to set in the sandbox container.",
    )
    pre_processor: Optional[str] = Field(
        default=None,
        deprecated=True,
        description="The pre-processing script to run before the experiment. Use the `/data/preprocessor` directory to load/store datasets. Deprecated in favor of `preprocessor`.",
    )
    preprocessor: Optional[str] = Field(
        default=None,
        description="A pre-processor script to run before the experiment. Use the `/data/preprocessor` directory to load/store datasets.",
    )
    services: Optional[list[ServiceConfig]] = Field(
        default=None,
        description="Additional services to run alongside the sandbox.",
    )


class PromptConfig(BaseModel):
    context: Optional[str] = Field(
        default=None,
        description="Some useful experiment-specific context to provide to the Hive.",
    )
    ideas: Optional[list[str]] = Field(
        default=None,
        description="A list of ideas which will be randomly sampled to inject into the Hive.",
    )
    enable_evolution: bool = Field(
        default=False,
        description="Whether to enable evolution for the experiment. Default to False.",
    )


class RepoConfig(BaseModel):
    source: str
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

    @field_validator("source")
    def source_should_not_be_git(cls, v):
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


class RuntimeConfig(BaseModel):
    num_agents: int = Field(
        default=1,
        description="Number of agents to use in the experiment. Default to 1.",
    )
    max_runtime_seconds: int = Field(
        default=-1,
        description="Maximum runtime for the experiment in seconds. \
            -1 means no limit.",
    )
    max_iterations: int = Field(
        default=-1,
        description="Maximum number of iterations for the experiment. \
            -1 means no limit.",
    )


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

    platform: PlatformType = Field(
        default=PlatformType.K8S,
        description="The platform type to use for the experiment. Default to 'k8s'.",
    )

    runtime: RuntimeConfig = Field(
        default_factory=RuntimeConfig, description="Runtime configuration for the experiment."
    )
    repo: RepoConfig = Field(
        default_factory=RepoConfig,
        description="Repository configuration for the experiment.",
    )
    sandbox: SandboxConfig = Field(
        default_factory=SandboxConfig,
        description="Sandbox configuration for the experiment.",
    )
    prompt: Optional[PromptConfig] = None

    # vendor configuration
    provider: ProviderConfig = Field(
        description="Provider configuration for the experiment.",
    )

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
