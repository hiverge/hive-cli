import argparse

from datetime import datetime
import yaml

def init(args):
    print("(Unimplemented) Initializing hive...")

def create(args):
    config_file = args.config

    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
            print(f"Configuration loaded successfully")
    except FileNotFoundError:
        print(f"Error: Config file '{config_file}' not found.")
        return
    except yaml.YAMLError as e:
        print(f"Error parsing YAML configuration: {e}")
        return

    if not validate_create(config):
        return


def validate_create(config):
    if not config.get("name") and not config.get("generateName"):
        print("Error: Either 'name' or 'generateName' must be specified in the configuration.")
        return False

def get_name(config) -> str:
    if config.get("name"):
        return config.get("name")
    elif config.get("generateName"):
        return config.get("generateName").format(datetime.now().strftime('%Y-%m-%d_%H%M%S'))
    # We should not reach here.
    return ""

def delete(args):
    print("Deleting hive...")

def login(args):
    print("(Unimplemented) Logging in to hive...")

def show_experiments(args):
    print("(Unimplemented) Showing experiments...")

def main():
    parser = argparse.ArgumentParser(description="Hive CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init command
    parser_init = subparsers.add_parser("init", help="Initialize hive")
    parser_init.set_defaults(func=init)

    # create command
    parser_create = subparsers.add_parser("create", help="Create a new hive")
    parser_create.add_argument("--config", required=False, help="Path to the hive configuration file, default to `hive.yaml`", default="hive.yaml")
    parser_create.add_argument("--platform", required=False, help="Platform to deploy the hive", default="k8s", choices=["k8s", "on-prem"])
    parser_create.set_defaults(func=create)

    # delete command
    parser_delete = subparsers.add_parser("delete", help="Delete a hive")
    parser_delete.set_defaults(func=delete)

    # login command
    parser_login = subparsers.add_parser("login", help="Login to hive")
    parser_login.set_defaults(func=login)

    # show command
    parser_show = subparsers.add_parser("show", help="Show resources")
    show_subparsers = parser_show.add_subparsers(dest="subcommand", required=True)

    # show experiments command
    parser_show_experiments = show_subparsers.add_parser("experiments", help="Show experiments")
    parser_show_experiments.set_defaults(func=show_experiments)

    args = parser.parse_args()
    args.func(args)
