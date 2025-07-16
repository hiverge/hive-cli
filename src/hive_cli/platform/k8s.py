import yaml

from .base import Platform

class K8sPlatform(Platform):
    def init(self, args):
        print("Initializing experiment on Kubernetes...")

    def create(self, args):
        print(f"Creating experiment on Kubernetes with name: {self.generate_experiment_name(args.name)}")
        config_file = args.config

        try:
            with open(config_file, 'r') as file:
                config = yaml.safe_load(file)
                print(f"Repository URL: {config.get('repo')}")
        except FileNotFoundError:
            print(f"Error: Config file '{config_file}' not found.")
            return
        except yaml.YAMLError as e:
            print(f"Error parsing YAML configuration: {e}")
            return

    def delete(self, args):
        print("Deleting experiment on Kubernetes...")

    def login(self, args):
        print("Logging in to hive on Kubernetes...")

    def show_experiments(self, args):
        print("Showing experiments on Kubernetes...")
