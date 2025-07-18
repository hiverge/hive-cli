from datetime import datetime

from kubernetes import client, config as k8s_config


class Runtime:
    def __init__(self, name: str):
        """Initialize the Runtime with a name.
        This can be used to set up any necessary runtime configurations.
        """

        self.experiment_name = generate_experiment_name(name)

        # Load the kube config.
        # This assumes you have a kubeconfig file at the default location (~/.kube/config)
        k8s_config.load_kube_config()
        self.k8s_client = client.CustomObjectsApi()


def generate_experiment_name(base_name: str) -> str:
    """
    Generate a unique experiment name based on the base name and current timestamp.
    If the base name ends with '-', it will be suffixed with a timestamp.
    """

    experiment_name = base_name

    if base_name.endswith("-"):
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        experiment_name = f"{base_name}{timestamp}"

    return experiment_name
