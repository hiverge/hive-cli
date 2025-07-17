from enum import Enum

from pydantic import BaseModel
import yaml

class PlatformType(str, Enum):
    K8S = "k8s"
    ON_PREM = "on-prem"

class CoordinatorConfig(BaseModel):
    pass

class EvaluatorConfig(BaseModel):
    timeout: int = 60

class RepoConfig(BaseModel):
    url: str

class WanDBConfig(BaseModel):
    enabled: bool = False

class HiveConfig(BaseModel):
    platform: PlatformType = PlatformType.K8S

    repo: RepoConfig
    # coordinator: CoordinatorConfig
    evaluator: EvaluatorConfig
    wandb: WanDBConfig

def load_config(file_path: str) -> HiveConfig:
    """Load configuration from a YAML file."""
    with open(file_path, 'r') as file:
        config_data = yaml.safe_load(file)
    return HiveConfig(**config_data)
