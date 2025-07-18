from kubernetes.client.rest import ApiException

from hive_cli.config import HiveConfig
from hive_cli.platform.base import Platform
from hive_cli.utils.logger import logger

GROUP = "core.hiverge.ai"
VERSION = "v1alpha1"
RESOURCE = "Experiment"
RESOURCE_PLURAL = "experiments"
# TODO: remove this once we support custom namespace
NAMESPACE = "default"


class K8sPlatform(Platform):
    def __init__(self, name: str):
        super().__init__(name)

    def create(self, config: HiveConfig):
        logger.info(f"Creating experiment '{self.experiment_name}' on Kubernetes...")

        config = self.setup_environment(config)
        self.deploy(config)

        logger.info(f"Launch experiment '{self.experiment_name}' successfully on Kubernetes.")

    def deploy(self, config: HiveConfig):
        logger.info(f"Deploying experiment '{self.experiment_name}' on Kubernetes...")

        body = construct_experiment(self.experiment_name, NAMESPACE, config)

        try:
            resp = self.k8s_client.create_namespaced_custom_object(
                group=GROUP, version=VERSION, namespace=NAMESPACE, plural=RESOURCE_PLURAL, body=body
            )
            logger.info(
                f"Experiment '{self.experiment_name}' deployed successfully on Kubernetes with name {resp['metadata']['name']}."
            )
        except ApiException as e:
            logger.error(f"Failed to create experiment '{self.experiment_name}' on Kubernetes: {e}")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while creating experiment '{self.experiment_name}': {e}"
            )

    def delete(self, name: str):
        logger.info(f"Deleting experiment '{self.experiment_name}' on Kubernetes...")
        try:
            # Attempt to delete the experiment by its name
            self.k8s_client.delete_namespaced_custom_object(
                group=GROUP,
                version=VERSION,
                namespace=NAMESPACE,
                plural=RESOURCE_PLURAL,
                name=name,
            )
            logger.info(f"Experiment '{name}' deleted successfully on Kubernetes.")
        except ApiException as e:
            logger.error(f"Failed to delete experiment '{name}' on Kubernetes: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while deleting experiment '{name}': {e}")

    def login(self, args):
        logger.info(f"Logging in to hive on {args.platform} platform...")

    def show_experiments(self, args):
        logger.info(f"Showing experiments on {args.platform} platform...")


def construct_experiment(name: str, namespace: str, config: HiveConfig) -> dict:
    """
    Constructs a Kubernetes custom resource definition (CRD) for an experiment.

    Args:
        name (str): The name of the experiment.
        namespace (str): The Kubernetes namespace where the experiment will be deployed.

    Returns:
        dict: A dictionary representing the CRD for the experiment.
    """
    return {
        "apiVersion": f"{GROUP}/{VERSION}",
        "kind": RESOURCE,
        "metadata": {
            "name": name,
            "namespace": namespace,
        },
        "spec": {
            "evaluator": {
                "image": config.evaluator.image,
                "replicas": config.evaluator.replicas,
                "timeout": config.evaluator.timeout,
            },
            "coordinator": {
                "image": config.coordinator.image,
            },
        },
    }
