"""Simple script to build, push, and deploy an experiment."""

import argparse
import getpass
import os
import subprocess
from datetime import datetime

from hive.logger import logger
from sandbox_utils import common_tools


def parse_args():
  """Parse the input specification and config arguments."""
  parser = argparse.ArgumentParser(
    description="Input specification and config of the experiment."
  )

  parser.add_argument("-p", "--project-id", type=str, help="GCP project id")
  parser.add_argument("-n", "--name", type=str, help="name of the sandbox")
  parser.add_argument(
    "-d", "--dockerfile_path", type=str, help="path to the Dockerfile"
  )
  parser.add_argument(
    "-w",
    "--where_to_deploy",
    type=str,
    choices=["gcr", "local"],
    default="gcr",
    help="where to deploy the sandbox (gcr or local)",
  )

  parser.add_argument("--timeout", type=str)
  parser.add_argument("--memory", type=str)
  parser.add_argument("--cpu", type=str)
  parser.add_argument("--concurrency", type=str)
  parser.add_argument("--min-instances", type=str)

  args = parser.parse_args()
  # Skip the name and dockerfile_path arguments as they are not gcloud args
  gcloud_args = {
    k: v
    for k, v in vars(args).items()
    if k not in ("name", "dockerfile_path", "project_id")
  }

  if args.name is None:
    args.name = (
      f"{getpass.getuser()}-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"
    )
  return (
    args.project_id,
    args.name,
    args.dockerfile_path,
    gcloud_args,
    args.where_to_deploy,
  )


def build_image(
  dockerfile_path: str,
  image_name: str,
  linux_amd_platform: bool = True,
  relative_path: str = ".",
) -> None:
  """Build the Docker image."""

  command = ["docker", "build"]
  if linux_amd_platform:
    command += ["--platform=linux/amd64"]
  command += ["-f", dockerfile_path, "-t", image_name, "."]
  subprocess.run(command, check=True, cwd=relative_path)


def push_image(
  image_name: str,
) -> None:
  """Push the Docker image to Google Container Registry."""

  try:
    subprocess.run(["docker", "push", image_name], check=True)
  except subprocess.CalledProcessError as e:
    raise RuntimeError(
      "Docker push has failed. Make sure you are logged in to Google Cloud"
      "\n\n\tgcloud auth application-default login\n\n"
      "and make sure Google Cloud has been authenticated with Docker"
      "\n\n\tgcloud auth configure-docker\n\n"
      "then try running this script again."
    ) from e


def deploy_cloud_run_sandbox(
  project_id: str,
  sandbox_name: str,
  args: dict,
) -> str:
  """Deploy a sandbox on Google Cloud Run."""

  optional_args = []
  for k, v in args.items():
    if v is not None:
      optional_args += [f"--{k}", v]

  subprocess.run(
    [
      "gcloud",
      "run",
      "deploy",
      sandbox_name,
      "--image",
      f"gcr.io/{project_id}/{sandbox_name}",
      "--platform",
      "managed",
      "--no-allow-unauthenticated",
    ]
    + optional_args,
    check=True,
  )

  output = subprocess.run(
    [
      "gcloud",
      "run",
      "services",
      "describe",
      sandbox_name,
      "--region",
      args["region"],
      "--platform",
      "managed",
      "--format",
      "value(status.url)",
    ],
    capture_output=True,
    text=True,
    check=True,
  )

  return output.stdout.strip()


def launch_sandbox(
  dockerfile_path: str,
  project_id: str,
  sandbox_name: str,
  deploy_optional_args: dict,
  where_to_deploy: str = "gcr",  # "gcr" or "local"
  verbose: bool = False,
  relative_path: str = ".",
) -> str:
  """Build, push, and deploy the sandbox."""

  logger.runtime.info(
    "Launching sandbox %s with Dockerfile %s in project %s",
    sandbox_name,
    dockerfile_path,
    project_id,
  )

  sandbox_name = sandbox_name.replace("_", "-").lower()
  image_name = f"{project_id}/{sandbox_name}"
  if where_to_deploy != "local":
    image_name = f"gcr.io/{image_name}"

  logger.runtime.debug(
    "Building image name %s for sandbox %s", image_name, sandbox_name
  )
  build_image(
    dockerfile_path,
    image_name,
    linux_amd_platform=where_to_deploy != "local",
    relative_path=relative_path,
  )

  if where_to_deploy == "local":
    logger.runtime.debug(
      "Running sandbox locally with image %s", image_name
    )
    subprocess.Popen(
      ["docker", "run", "-p", "8080:8080", image_name],
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
    )
    # Wait for the server to start
    common_tools.wait_for_url("http://localhost:8080/health")
    logger.runtime.debug(
      "Sandbox is running locally at http://localhost:8080"
    )
    return "http://localhost:8080"

  # If here, we are deploying to Google Cloud Run
  # TODO(Add option to deploy to GKE)
  logger.runtime.debug(
    "Pushing Docker image %s to Google Container Registry", image_name
  )
  push_image(image_name)

  logger.runtime.debug(
    "Deploying sandbox %s on Google Cloud Run with project %s",
    sandbox_name,
    project_id,
  )
  return deploy_cloud_run_sandbox(
    project_id, sandbox_name, deploy_optional_args
  )


def get_relative_path() -> str:
  """Get the relative path to the current working directory."""
  cwd = os.getcwd()
  if cwd.endswith("hiverge"):
    return "."
  elif cwd.endswith("hiverge/sandbox_utils"):
    return ".."
  else:
    raise RuntimeError(
      f"Please run this script from the hiverge directory instead of {cwd}."
    )


if __name__ == "__main__":
  relative_path = get_relative_path()
  (
    project_id,
    sandbox_name,
    dockerfile_path,
    deploy_optional_args,
    where_to_deploy,
  ) = parse_args()
  sandbox_url = launch_sandbox(
    dockerfile_path,
    project_id,
    sandbox_name,
    deploy_optional_args,
    where_to_deploy,
    verbose=True,
    relative_path=relative_path,
  )
  print(f"\n\nSandbox is now available at {sandbox_url}\n")
