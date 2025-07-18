import argparse

from hive_cli.config import load_config
from hive_cli.platform.k8s import K8sPlatform
from hive_cli.platform.onprem import OnPremPlatform

PLATFORMS = {
    "k8s": K8sPlatform,
    "on-prem": OnPremPlatform,
}


def init(args):
    print("(Unimplemented) Initializing hive...")


def create(args):
    config = load_config(args.config)
    # Init the platform based on the config.
    platform = PLATFORMS[config.platform.value](args.name)

    platform.create(config=config)


def delete(args):
    platform = PLATFORMS[args.platform](args.platform)
    platform.delete(args.name)


def main():
    blue = "\033[34m"
    reset = "\033[0m"
    print(f"{blue}█████   █████  ███                      ")
    print("░░███   ░░███  ░░░                       ")
    print(" ░███    ░███  ████  █████ █████  ██████ ")
    print(" ░███████████ ░░███ ░░███ ░░███  ███░░███")
    print(" ░███░░░░░███  ░███  ░███  ░███ ░███████ ")
    print(" ░███    ░███  ░███  ░░███ ███  ░███░░░  ")
    print(" █████   █████ █████  ░░█████   ░░██████ ")
    print(f"░░░░░   ░░░░░ ░░░░░    ░░░░░     ░░░░░░  {reset}")

    parser = argparse.ArgumentParser(description="Hive CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init command
    parser_init = subparsers.add_parser("init", help="Initialize a repository")
    parser_init.set_defaults(func=init)

    # create command
    parser_create = subparsers.add_parser("create", help="Create a new experiment")
    parser_create.add_argument(
        "name",
        help="Name of the experiment to create. If ends with `-`, it will be generated with a timestamp suffix like `exper-2023-10-01_123456`",
    )
    parser_create.add_argument(
        "-f", "--config", required=True, help="Path to the experiment configuration file"
    )
    parser_create.set_defaults(func=create)

    # delete command
    parser_delete = subparsers.add_parser("delete", help="Delete a experiment")
    parser_delete.add_argument("name", help="Name of the experiment to delete")
    parser_delete.add_argument(
        "-p",
        "--platform",
        default="k8s",
        choices=PLATFORMS.keys(),
        help="Platform to use, k8s or on-prem, default to use k8s",
    )
    parser_delete.set_defaults(func=delete)

    args = parser.parse_args()
    args.func(args)
