from enum import Enum
from typing import Optional

import yaml
from pydantic import BaseModel, Field, field_validator


class PlatformType(str, Enum):
    K8S = "k8s"
    ON_PREM = "on-prem"


class ResourceConfig(BaseModel):
    requests: Optional[dict] = None
    limits: Optional[dict] = None
    accelerators: Optional[str] = None  # e.g., "a100-80gb:8"
    shmsize: Optional[str] = None


class EnvConfig(BaseModel):
    name: str
    value: str


class SandboxConfig(BaseModel):
    image: Optional[str] = None
    replicas: int = 1
    timeout: int = 60
    resources: Optional[ResourceConfig] = None
    envs: Optional[list[EnvConfig]] = None
    pre_processor: Optional[str] = Field(
        default=None,
        description="The pre-processing script to run before the experiment. Use the `/data` directory to load/store datasets.",
    )


class RepoConfig(BaseModel):
    url: str
    branch: str = "main"
    evaluation_script: str = "evaluator.py"
    evolve_files_and_ranges: str


class WanDBConfig(BaseModel):
    enabled: bool = False


class GCPConfig(BaseModel):
    enabled: bool = False
    project_id: str = Field(
        default="runsandbox-449400",
        description="The GCP project ID to use for the experiment.",
    )
    image_registry: str | None = Field(
        default=None,
        description="The GCP image registry to use for the experiment images. If not set, will use the default GCP registry.",
    )


class AWSConfig(BaseModel):
    enabled: bool = False
    image_registry: str | None = Field(
        default=None,
        description="The AWS image registry to use for the experiment images. If not set, will use the default AWS ECR registry.",
    )


class DashboardConfig(BaseModel):
    enabled: bool = False


class CloudProviderConfig(BaseModel):
    spot: bool = False
    gcp: Optional[GCPConfig] = None
    aws: Optional[AWSConfig] = None


class HiveConfig(BaseModel):
    project_name: (
        str  # project_name is for a specific project, like the beluga-direct-plan-project.
    )

    coordinator_config_name: str = "default-coordinator-config"
    dashboard: DashboardConfig

    platform: PlatformType = PlatformType.K8S

    repo: RepoConfig
    sandbox: SandboxConfig
    wandb: WanDBConfig

    # cloud vendor configuration
    cloud_provider: CloudProviderConfig

    @field_validator("project_name")
    def must_be_lowercase(cls, v):
        if not v.islower():
            raise ValueError("project_name must be all lowercase")
        return v

    def model_post_init(self, __context):
        if (
            self.cloud_provider.gcp
            and self.cloud_provider.gcp.enabled
            and not self.cloud_provider.gcp.image_registry
        ):
            self.cloud_provider.gcp.image_registry = (
                f"gcr.io/{self.cloud_provider.gcp.project_id}/{self.project_name}"
            )

        if (
            self.cloud_provider.aws
            and self.cloud_provider.aws.enabled
            and not self.cloud_provider.aws.image_registry
        ):
            self.cloud_provider.aws.image_registry = (
                f"621302123805.dkr.ecr.eu-north-1.amazonaws.com/hiverge/{self.project_name}"
            )


def load_config(file_path: str) -> HiveConfig:
    """Load configuration from a YAML file."""
    with open(file_path, "r") as file:
        config_data = yaml.safe_load(file)
    return HiveConfig(**config_data)
