from hive_cli.config import HiveConfig

from .base import Platform


class OnPremPlatform(Platform):
    def __init__(self, exp_name: str | None, token_path: str = None):
        super().__init__(exp_name, token_path)

    def create(self, config: HiveConfig):
        print(f"Creating hive on-premise with name: {self.experiment_name} and config: {config}")

    def update(self, name: str, config: HiveConfig):
        print(f"Updating hive on-premise with name: {name} and config: {config}")

    def delete(self, name: str):
        print("Deleting hive on-premise...")

    def login(self, args):
        print("Logging in to hive on-premise...")

    def show_experiments(self, args):
        print("Showing experiments on-premise...")

    def show_sandboxes(self, args):
        print("Showing sandboxes on-premise...")

    def log(self, args):
        print("Showing logs for sandbox:", args.sandbox)
