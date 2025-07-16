from .base import Platform

class OnPremPlatform(Platform):
    def init(self, args):
        print("Initializing hive on-premise...")

    def create(self, args):
        print(f"Creating hive on-premise with config: {args.config}")

    def delete(self, args):
        print("Deleting hive on-premise...")

    def login(self, args):
        print("Logging in to hive on-premise...")

    def show_experiments(self, args):
        print("Showing experiments on-premise...")
