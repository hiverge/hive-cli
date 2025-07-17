from hive_cli.config import HiveConfig
from hive_cli.platform.base import Platform
from hive_cli.utils.logger import logger

class K8sPlatform(Platform):
    def __init__(self, name: str):
        super().__init__(name)

    def create(self, config: HiveConfig):
        logger.info(f"Creating experiment '{self.experiment_name}' on Kubernetes...")

        self.setup_environment(config)

        logger.info(f"Experiment '{self.experiment_name}' created successfully on Kubernetes.")

    def deploy(self, config: HiveConfig):
        logger.info(f"Deploying experiment '{self.experiment_name}' on Kubernetes...")

    def delete(self, args):
        logger.info(f"Deleting experiment '{self.experiment_name}' on {args.platform} platform...")
        self.cleanup_environment(self.experiment_name)

    def login(self, args):
        logger.info(f"Logging in to hive on {args.platform} platform...")

    def show_experiments(self, args):
        logger.info(f"Showing experiments on {args.platform} platform...")
