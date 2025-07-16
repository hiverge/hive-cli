import argparse

from .platform.k8s import K8sPlatform
from .platform.onprem import OnPremPlatform

PLATFORMS = {
    "k8s": K8sPlatform,
    "on-prem": OnPremPlatform,
}

def main():
    parser = argparse.ArgumentParser(description="Hive CLI")
    parser.add_argument("-p", "--platform", default="k8s", choices=PLATFORMS.keys(), help="Platform to use, k8s or on-prem, default to use k8s")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init command
    parser_init = subparsers.add_parser("init", help="Initialize a repository")
    parser_init.set_defaults(func=lambda args: PLATFORMS[args.platform]().init(args))

    # create command
    parser_create = subparsers.add_parser("create", help="Create a new experiment")
    parser_create.add_argument("name", help="Name of the experiment to create. If ends with `-`, it will be generated with a timestamp suffix like `exper-2023-10-01_123456`")
    parser_create.add_argument("-f", "--config", required=True, help="Path to the experiment configuration file")
    parser_create.set_defaults(func=lambda args: PLATFORMS[args.platform]().create(args))

    # delete command
    parser_delete = subparsers.add_parser("delete", help="Delete a experiment")
    parser_delete.add_argument("name", help="Name of the experiment to delete")
    parser_delete.set_defaults(func=lambda args: PLATFORMS[args.platform]().delete(args))

    # TODO:
    # # login command
    # parser_login = subparsers.add_parser("login", help="Login to Hive")
    # parser_login.set_defaults(func=lambda args: PLATFORMS[args.platform]().login(args))

    # # show command
    # parser_show = subparsers.add_parser("show", help="Show resources")
    # show_subparsers = parser_show.add_subparsers(dest="subcommand", required=True)

    # # show experiments command
    # parser_show_experiments = show_subparsers.add_parser("experiments", help="Show experiments")
    # parser_show_experiments.set_defaults(func=lambda args: PLATFORMS[args.platform]().show_experiments(args))

    args = parser.parse_args()
    args.func(args)
