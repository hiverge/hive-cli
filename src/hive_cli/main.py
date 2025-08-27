import argparse
import os
import subprocess
from importlib.metadata import PackageNotFoundError, version

import portforward
from rich.console import Console
from rich.text import Text

from hive_cli.config import load_config
from hive_cli.platform.k8s import K8sPlatform
from hive_cli.utils import event

try:
    __version__ = version("hiverge-cli")
except PackageNotFoundError:
    __version__ = "unknown"


PLATFORMS = {
    "k8s": K8sPlatform,
    # "on-prem": OnPremPlatform,
}


def init(args):
    print("(Unimplemented) Initializing hive...")


def create_experiment(args):
    BLUE = "\033[94m"
    RESET = "\033[0m"

    ascii_art = r"""
     ███          █████   █████  ███
    ░░░███       ░░███   ░░███  ░░░
      ░░░███      ░███    ░███  ████  █████ █████  ██████
        ░░░███    ░███████████ ░░███ ░░███ ░░███  ███░░███
         ███░     ░███░░░░░███  ░███  ░███  ░███ ░███████
       ███░       ░███    ░███  ░███  ░░███ ███  ░███░░░
     ███░         █████   █████ █████  ░░█████   ░░██████
    ░░░          ░░░░░   ░░░░░ ░░░░░    ░░░░░     ░░░░░░
    """

    print(f"{BLUE}{ascii_art}{RESET}")

    config = load_config(args.config)
    # Init the platform based on the config.
    platform = PLATFORMS[config.platform.value](args.name, config.token_path)

    platform.create(config=config)


def update_experiment(args):
    config = load_config(args.config)
    # Init the platform based on the config.
    platform = PLATFORMS[config.platform.value](args.name, config.token_path)

    platform.update(args.name, config=config)

    console = Console()
    msg = Text(f"Experiment {args.name} updated successfully.", style="bold green")
    console.print(msg)


def delete_experiment(args):
    config = load_config(args.config)

    platform = PLATFORMS[args.platform](args.platform, config.token_path)
    platform.delete(args.name)


def show_experiment(args):
    config = load_config(args.config)

    platform = PLATFORMS[args.platform](args.platform, config.token_path)
    platform.show_experiments(args)


def edit(args):
    editor = os.environ.get("EDITOR", "vim")
    subprocess.run([editor, args.config])

    console = Console()
    msg = Text(args.config, style="bold magenta")
    msg.append(" edited successfully.", style="bold green")
    console.print(msg)


def show_dashboard(args):
    config = load_config(args.config)
    platform = PLATFORMS[args.platform](args.platform, config.token_path)
    core_v1 = platform.core_client

    console = Console()
    url = f"http://localhost:{args.port}"
    msg = Text("Hive-Dashboard is available at ", style="bold green")
    msg.append(url, style="bold magenta")
    msg.append(" ...", style="dim")
    console.print(msg)

    # TODO: support user namespace
    namespace = "default"
    svc_name = "hive-dashboard-frontend"
    remote_port = 3000

    svc = core_v1.read_namespaced_service(svc_name, namespace)
    selector = svc.spec.selector
    label_selector = ",".join([f"{k}={v}" for k, v in selector.items()])
    pods = core_v1.list_namespaced_pod(namespace, label_selector=label_selector)
    if not pods.items:
        console.print("[bold red]No dashboard available now[/]")
        return
    pod_name = pods.items[0].metadata.name

    with portforward.forward(namespace, pod_name, args.port, remote_port, config.token_path):
        event.wait_for_ctrl_c()
        console.print("\n[bold yellow]Port forwarding stopped.[/]")


def main():
    parser = argparse.ArgumentParser(description="Hive CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # TODO:
    # # init command
    # parser_init = subparsers.add_parser("init", help="Initialize a repository")
    # parser_init.set_defaults(func=init)

    # create command
    parser_create = subparsers.add_parser("create", help="Create resources")
    create_subparsers = parser_create.add_subparsers(dest="create_target")

    parser_create_exp = create_subparsers.add_parser(
        "experiment", aliases=["exp"], help="Create a new experiment"
    )
    parser_create_exp.add_argument(
        "name",
        help="Name of the experiment, if it ends with '-', a timestamp will be appended. Example: 'exp-' will become 'exp-2023-10-01-123456'",
    )
    parser_create_exp.add_argument(
        "-f",
        "--config",
        default=os.path.expandvars("$HOME/.hive/sandbox-config.yaml"),
        help="Path to the config file, default to ~/.hive/sandbox-config.yaml",
    )
    parser_create_exp.set_defaults(func=create_experiment)

    # TODO:
    # update command
    # parser_update = subparsers.add_parser("update", help="Update resources")
    # update_subparsers = parser_update.add_subparsers(dest="update_target")

    # parser_update_exp = update_subparsers.add_parser(
    #     "experiment", aliases=["exp"], help="Update an experiment"
    # )
    # parser_update_exp.add_argument("name", help="Name of the experiment")
    # parser_update_exp.add_argument(
    #     "-f",
    #     "--config",
    #     default=os.path.expandvars("$HOME/.hive/sandbox-config.yaml"),
    #     help="Path to the config file, default to ~/.hive/sandbox-config.yaml",
    # )
    # parser_update_exp.set_defaults(func=update_experiment)

    # delete command
    parser_delete = subparsers.add_parser("delete", help="Delete resources")
    delete_subparsers = parser_delete.add_subparsers(dest="delete_target")
    parser_delete_exp = delete_subparsers.add_parser(
        "experiment", aliases=["exp"], help="Delete an experiment"
    )
    parser_delete_exp.add_argument("name", help="Name of the experiment")
    parser_delete_exp.add_argument(
        "-p",
        "--platform",
        default="k8s",
        choices=PLATFORMS.keys(),
        help="Platform to use, k8s or on-prem, default to use k8s",
    )
    parser_delete_exp.add_argument(
        "-f",
        "--config",
        default=os.path.expandvars("$HOME/.hive/sandbox-config.yaml"),
        help="Path to the config file, default to ~/.hive/sandbox-config.yaml",
    )
    parser_delete_exp.set_defaults(func=delete_experiment)

    # show command
    parser_show = subparsers.add_parser("show", help="Show resources")
    show_subparsers = parser_show.add_subparsers(dest="show_target")
    parser_show_exp = show_subparsers.add_parser(
        "experiments", aliases=["exp", "exps"], help="Show experiments"
    )
    parser_show_exp.add_argument(
        "-p",
        "--platform",
        default="k8s",
        choices=PLATFORMS.keys(),
        help="Platform to use, k8s or on-prem, default to use k8s",
    )
    parser_show_exp.add_argument(
        "-f",
        "--config",
        default=os.path.expandvars("$HOME/.hive/sandbox-config.yaml"),
        help="Path to the config file, default to ~/.hive/sandbox-config.yaml",
    )
    parser_show_exp.set_defaults(func=show_experiment)

    # edit command
    parser_edit = subparsers.add_parser("edit", help="Edit Hive configuration")
    edit_subparsers = parser_edit.add_subparsers(dest="edit_target")
    parser_edit_config = edit_subparsers.add_parser(
        "config", help="Edit the Hive configuration file"
    )
    parser_edit_config.add_argument(
        "-f",
        "--config",
        default=os.path.expandvars("$HOME/.hive/sandbox-config.yaml"),
        help="Path to the config file, defaults to ~/.hive/sandbox-config.yaml",
    )
    parser_edit_config.set_defaults(func=edit)

    # dashboard command
    parser_dashboard = subparsers.add_parser("dashboard", help="Open the Hive dashboard")
    parser_dashboard.add_argument(
        "--port",
        default=9090,
        type=int,
        help="Port to run the dashboard on, default to 9090",
    )
    parser_dashboard.add_argument(
        "-f",
        "--config",
        default=os.path.expandvars("$HOME/.hive/sandbox-config.yaml"),
        help="Path to the config file, default to ~/.hive/sandbox-config.yaml",
    )
    parser_dashboard.add_argument(
        "-p",
        "--platform",
        default="k8s",
        choices=PLATFORMS.keys(),
        help="Platform to use, k8s or on-prem, default to use k8s",
    )
    parser_dashboard.set_defaults(func=show_dashboard)

    # version command
    parser_version = subparsers.add_parser("version", help="Show Hive CLI version")
    parser_version.set_defaults(func=lambda args: print(f"Hive CLI version {__version__}"))

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
