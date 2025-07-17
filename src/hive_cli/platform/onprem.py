from hive_cli.config import HiveConfig
from .base import Platform

class OnPremPlatform(Platform):
    def create(self, name: str, config: HiveConfig):
        print(f"Creating hive on-premise with name: {name} and config: {config}")

    def delete(self, args):
        print("Deleting hive on-premise...")

    def login(self, args):
        print("Logging in to hive on-premise...")

    def show_experiments(self, args):
        print("Showing experiments on-premise...")
