from kubernetes import client, watch
from kubernetes import config as k8s_config
from kubernetes.client.api_client import ApiClient
from kubernetes.client.rest import ApiException
from rich.console import Console
from rich.table import Table

from hive_cli.config import HiveConfig
from hive_cli.platform.base import Platform
from hive_cli.utils.logger import logger
from hive_cli.utils.time import humanize_time

GROUP = "core.hiverge.ai"
VERSION = "v1alpha1"
RESOURCE = "Experiment"
RESOURCE_PLURAL = "experiments"
# TODO: remove this once we support custom namespace
NAMESPACE = "default"
EXPERIMENT_NAME_LABEL = "hiverge.ai/experiment-name"
SANDBOX_LABEL_SELECTOR = "app=hive-sandbox"


class K8sPlatform(Platform):
    def __init__(self, exp_name: str | None, token_path: str = None):
        super().__init__(exp_name, token_path)

        k8s_config.load_kube_config(config_file=token_path)
        self.client = client.CustomObjectsApi()
        self.core_client = client.CoreV1Api()

    def create(self, config: HiveConfig):
        logger.info(f"Creating experiment '{self.experiment_name}' on Kubernetes...")
        config = self.setup_environment(config)
        deploy("CREATE", self.client, self.experiment_name, config)

    def update(self, name: str, config: HiveConfig):
        logger.info(f"Updating experiment '{name}' on Kubernetes...")
        deploy("UPDATE", self.client, name, config)

    def delete(self, name: str):
        logger.info(f"Deleting experiment '{name}' on Kubernetes...")
        try:
            # Attempt to delete the experiment by its name
            self.client.delete_namespaced_custom_object(
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
        resp = self.client.list_namespaced_custom_object(
            group=GROUP,
            version=VERSION,
            namespace=NAMESPACE,
            plural=RESOURCE_PLURAL,
        )

        table = Table(show_header=True, header_style="bold", box=None, show_lines=False)
        table.add_column("Name")
        table.add_column("Status")
        table.add_column("Sandboxes")
        table.add_column("Age")

        for item in resp.get("items", []):
            metadata = item.get("metadata", {})
            age = humanize_time(metadata.get("creationTimestamp"))
            status = item.get("status", {}).get("phase", "Unknown")
            replicas = item.get("status", {}).get("sandboxReplicas", 0)
            unavailable_replicas = item.get("status", {}).get("sandboxUnavailableReplicas", 0)

            table.add_row(
                metadata.get("name", "Unknown"),
                status,
                f"{replicas - unavailable_replicas}/{replicas}",
                age if age else "N/A",
            )

        console = Console()
        console.print(table)

    def show_sandboxes(self, args):
        experiment_name = args.experiment

        if experiment_name:
            pods = self.core_client.list_namespaced_pod(
                namespace=NAMESPACE,
                label_selector=f"{SANDBOX_LABEL_SELECTOR},{EXPERIMENT_NAME_LABEL}={experiment_name}",
            )
        else:
            pods = self.core_client.list_namespaced_pod(
                namespace=NAMESPACE, label_selector=SANDBOX_LABEL_SELECTOR
            )

        table = Table(show_header=True, header_style="bold", box=None, show_lines=False)
        table.add_column("Name")
        table.add_column("Experiment")
        table.add_column("Status")
        table.add_column("Restarts")
        table.add_column("Age")

        for pod in pods.items:
            restarts = 0

            for cs in pod.status.container_statuses or []:
                restarts += cs.restart_count

            table.add_row(
                pod.metadata.name,
                pod.metadata.labels.get(EXPERIMENT_NAME_LABEL, "Unknown"),
                pod.status.phase,
                str(restarts),
                humanize_time(pod.metadata.creation_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")),
            )

        console = Console()
        console.print(table)

    def log(self, args):
        w = watch.Watch()

        try:
            for event in w.stream(
                self.core_client.read_namespaced_pod_log,
                name=args.sandbox,
                namespace=NAMESPACE,
                container="sandbox",
                follow=True,
                tail_lines=args.tail,
            ):
                print(event)
        except KeyboardInterrupt:
            # Ignore the error.
            pass
        except ApiException as e:
            logger.error(f"Failed to fetch logs for sandbox '{args.sandbox}': {e}")
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while fetching logs for sandbox '{args.sandbox}': {e}"
            )


def deploy(op: str, client: ApiClient, name: str, config: HiveConfig):
    logger.info(f"Applying experiment '{name}' on Kubernetes...")

    body = construct_experiment(name, NAMESPACE, config)

    try:
        if op == "CREATE":
            resp = client.create_namespaced_custom_object(
                group=GROUP, version=VERSION, namespace=NAMESPACE, plural=RESOURCE_PLURAL, body=body
            )
            logger.info(
                f"Experiment '{name}' created successfully on Kubernetes with name {resp['metadata']['name']}."
            )
        # TODO: add validation for op, only replicas can be updated
        elif op == "UPDATE":
            current_exp = client.get_namespaced_custom_object(
                group=GROUP, version=VERSION, namespace=NAMESPACE, plural=RESOURCE_PLURAL, name=name
            )

            # Populate some fields manually because they're generated in creation.
            if body["spec"]["sandbox"].get("image") is None:
                body["spec"]["sandbox"]["image"] = current_exp["spec"]["sandbox"]["image"]

            resp = client.patch_namespaced_custom_object(
                group=GROUP,
                version=VERSION,
                namespace=NAMESPACE,
                plural=RESOURCE_PLURAL,
                name=name,
                body=body,
            )
            logger.info(
                f"Experiment '{name}' updated successfully on Kubernetes with name {resp['metadata']['name']}."
            )
        else:
            raise ValueError(
                f"Unsupported operation: {op}. Supported operations are 'CREATE' and 'UPDATE'."
            )
    except ApiException as e:
        logger.error(f"Failed to deploy experiment '{name}' on Kubernetes: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while deploying experiment '{name}': {e}")


def construct_experiment(name: str, namespace: str, config: HiveConfig) -> dict:
    """
    Constructs a Kubernetes custom resource definition (CRD) for an experiment.

    Args:
        name (str): The name of the experiment.
        namespace (str): The Kubernetes namespace where the experiment will be deployed.

    Returns:
        dict: A dictionary representing the CRD for the experiment.
    """

    if config.provider.gcp and config.provider.gcp.enabled:
        provider_name = "gcp"
        spot = config.provider.gcp.spot
    elif config.provider.aws and config.provider.aws.enabled:
        provider_name = "aws"
        spot = config.provider.aws.spot
    else:
        provider_name = "unknown"
        spot = False

    if config.sandbox.envs is not None:
        envs = [env.model_dump() for env in config.sandbox.envs]
    else:
        envs = None

    resources = {}
    if config.sandbox.resources is not None:
        # We keep the requests and limits in the experiment spec to maintain extensibility.
        # Always keep requests and limits the same to avoid resource competition.
        resources = {
            "requests": {
                "cpu": config.sandbox.resources.cpu,
                "memory": config.sandbox.resources.memory,
            },
            "limits": {
                "cpu": config.sandbox.resources.cpu,
                "memory": config.sandbox.resources.memory,
            },
            "shmSize": config.sandbox.resources.shmsize,
            "accelerators": config.sandbox.resources.accelerators,
        }

        if config.sandbox.resources.extended_resources is not None:
            resources["requests"].update(config.sandbox.resources.extended_resources)
            resources["limits"].update(config.sandbox.resources.extended_resources)

    services = []
    if config.sandbox.services is not None:
        for svc in config.sandbox.services:
            svc_dict = {
                "name": svc.name,
                "image": svc.image,
                "envs": [env.model_dump() for env in svc.envs] if svc.envs else None,
                "command": svc.command,
                "args": svc.args,
                "resources": {
                    "requests": {
                        "cpu": svc.resources.cpu,
                        "memory": svc.resources.memory,
                    },
                    "limits": {
                        "cpu": svc.resources.cpu,
                        "memory": svc.resources.memory,
                    },
                    "shmSize": svc.resources.shmsize,
                    "accelerators": svc.resources.accelerators,
                },
            }
            if svc.ports is not None:
                for port in svc.ports:
                    if "ports" not in svc_dict:
                        svc_dict["ports"] = []
                    svc_dict["ports"].append(
                        {
                            "name": svc.name + "-" + str(port.port),
                            "containerPort": port.port,
                            "protocol": port.protocol,
                        }
                    )

            if svc.resources.extended_resources is not None:
                svc_dict["resources"]["requests"].update(svc.resources.extended_resources)
                svc_dict["resources"]["limits"].update(svc.resources.extended_resources)

            services.append(svc_dict)

    result = {
        "apiVersion": f"{GROUP}/{VERSION}",
        "kind": RESOURCE,
        "metadata": {
            "name": name,
            "namespace": namespace,
        },
        "spec": {
            "projectName": config.project_name,
            "coordinatorConfigName": config.coordinator_config_name,
            "sandbox": {
                "image": config.sandbox.image,
                "timeout": config.sandbox.timeout,
                "resources": resources,
                "envs": envs,
                "preprocessor": config.sandbox.pre_processor or config.sandbox.preprocessor,
                "services": services,
            },
            "repo": {
                "branch": config.repo.branch,
                "evaluationScript": config.repo.evaluation_script,
                "evolveFilesAndRanges": config.repo.evolve_files_and_ranges,
                "includeFilesAndRanges": config.repo.include_files_and_ranges,
            },
            "provider": {
                "spot": spot,
                "name": provider_name,
            },
            "runtime": {
                "numAgents": config.runtime.num_agents,
                "maxRuntimeSeconds": config.runtime.max_runtime_seconds,
                "maxIterations": config.runtime.max_iterations,
            },
        },
    }

    if config.prompt:
        result["spec"]["prompt"] = {
            "enableEvolution": config.prompt.enable_evolution,
            "context": config.prompt.context,
            "ideas": config.prompt.ideas,
        }

    return result
