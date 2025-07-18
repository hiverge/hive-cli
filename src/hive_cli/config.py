from enum import Enum
from typing import Optional

import yaml
from pydantic import BaseModel


class PlatformType(str, Enum):
    K8S = "k8s"
    ON_PREM = "on-prem"


class CoordinatorConfig(BaseModel):
    image: str


class EvaluatorConfig(BaseModel):
    image: Optional[str] = None
    replicas: int = 1
    timeout: int = 60


class RepoConfig(BaseModel):
    url: str
    branch: str = "main"


class WanDBConfig(BaseModel):
    enabled: bool = False


class GCPConfig(BaseModel):
    project_id: str


class HiveConfig(BaseModel):
    project_name: (
        str  # project_name is for a specific project, like the beluga-direct-plan-project.
    )
    platform: PlatformType = PlatformType.K8S

    repo: RepoConfig
    coordinator: CoordinatorConfig
    evaluator: EvaluatorConfig
    wandb: WanDBConfig

    # cloud vendor configuration
    gcp: Optional[GCPConfig] = None


def load_config(file_path: str) -> HiveConfig:
    """Load configuration from a YAML file."""
    with open(file_path, "r") as file:
        config_data = yaml.safe_load(file)
    return HiveConfig(**config_data)
