"""
Argcomplete completer functions for the Hive CLI.

These functions provide dynamic tab completion for commands, fetching
resource names from Kubernetes and providing file path completion.
"""

import os
import signal
from functools import wraps

from argcomplete.completers import FilesCompleter


def safe_completer(func):
    """
    Decorator to wrap completer functions with error handling.

    Ensures that completers never raise exceptions that would break the CLI.
    All errors are silently caught and an empty list is returned.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            # Silent failure - return empty list on any error
            return []
    return wrapper


class TimeoutError(Exception):
    """Raised when a completion operation times out."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Operation timed out")


@safe_completer
def experiment_completer(prefix, parsed_args, **kwargs):
    """
    Complete experiment names by fetching from Kubernetes.

    Used for:
    - hive delete experiment <name>
    - hive show sandboxes --experiment <name>

    Args:
        prefix: The current prefix being completed
        parsed_args: Parsed arguments from argparse
        **kwargs: Additional arguments from argcomplete

    Returns:
        List of experiment names matching the prefix
    """
    # Set up 2-second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(2)

    try:
        # Import here to avoid loading K8s client at module import time
        from hive_cli.config import load_config
        from hive_cli.platform.k8s import K8sPlatform

        # Load config - use default if not specified
        config_path = getattr(parsed_args, "config", None)
        if not config_path:
            config_path = os.path.expandvars("$HOME/.hive/hive.yaml")

        config = load_config(config_path)

        # Create platform and fetch experiments
        platform = K8sPlatform(None, config.token_path)
        resp = platform.client.list_namespaced_custom_object(
            group="core.hiverge.ai",
            version="v1alpha1",
            namespace="default",
            plural="experiments",
        )

        # Extract experiment names
        experiments = [item["metadata"]["name"] for item in resp.get("items", [])]

        # Filter by prefix if provided
        if prefix:
            experiments = [exp for exp in experiments if exp.startswith(prefix)]

        return experiments

    except TimeoutError:
        # Timeout - return empty list
        return []
    finally:
        # Cancel alarm
        signal.alarm(0)


@safe_completer
def sandbox_completer(prefix, parsed_args, **kwargs):
    """
    Complete sandbox pod names by fetching from Kubernetes.

    Used for:
    - hive log <sandbox-name>

    If --experiment flag is provided, filters sandboxes by experiment label.

    Args:
        prefix: The current prefix being completed
        parsed_args: Parsed arguments from argparse
        **kwargs: Additional arguments from argcomplete

    Returns:
        List of sandbox pod names matching the prefix
    """
    # Set up 2-second timeout
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(2)

    try:
        # Import here to avoid loading K8s client at module import time
        from hive_cli.config import load_config
        from hive_cli.platform.k8s import K8sPlatform

        # Load config - use default if not specified
        config_path = getattr(parsed_args, "config", None)
        if not config_path:
            config_path = os.path.expandvars("$HOME/.hive/hive.yaml")

        config = load_config(config_path)

        # Create platform and fetch sandboxes
        platform = K8sPlatform(None, config.token_path)

        # Build label selector
        label_selector = "app=hive-sandbox"

        # Filter by experiment if provided
        experiment = getattr(parsed_args, "experiment", None)
        if experiment:
            label_selector += f",hiverge.ai/experiment-name={experiment}"

        # Fetch pods
        pods = platform.core_client.list_namespaced_pod(
            namespace="default",
            label_selector=label_selector
        )

        # Extract sandbox names
        sandboxes = [pod.metadata.name for pod in pods.items]

        # Filter by prefix if provided
        if prefix:
            sandboxes = [sb for sb in sandboxes if sb.startswith(prefix)]

        return sandboxes

    except TimeoutError:
        # Timeout - return empty list
        return []
    finally:
        # Cancel alarm
        signal.alarm(0)


def config_file_completer(prefix, parsed_args, **kwargs):
    """
    Complete config file paths for -f/--config flags.

    Delegates to argcomplete's built-in FilesCompleter for file path completion.

    Args:
        prefix: The current prefix being completed
        parsed_args: Parsed arguments from argparse
        **kwargs: Additional arguments from argcomplete

    Returns:
        List of file paths matching the prefix
    """
    return FilesCompleter()(prefix, **kwargs)
