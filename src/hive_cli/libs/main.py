"""A simple Python sandbox server that executes Python functions."""

import aiohttp
import asyncio
import logging
import os
import subprocess
import tempfile
from typing import Any
import json

from hive_cli.libs import common_tools, overlay

REPO_DIR = "/app/repo"  # Directory where the repository is mounted
SERVER_ERROR = "Problem with the server."

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_to_server(
  data: dict[str, Any],
  endpoint: str,
  initial_delay: float,
  delay_multiplier: float,
  request_timeout: float,
) -> str:
  """Sends data to the server and returns the response and the time it took."""
  headers = {"Content-Type": "application/json"}

  delay = initial_delay  # start with 1 second
  attempt = 1
  while True:
    timeout = aiohttp.ClientTimeout(
      total=request_timeout, connect=300, sock_connect=30
    )
    async with (
      aiohttp.ClientSession(
        timeout=timeout
      ) as session,
      session.post(endpoint, json=data, headers=headers) as response,
    ):
      match response.status:
        case 200:
          text_response = await response.text()
          break
        case _:
          logger.error(
            f"Response status: {response.status}. Attempt #{attempt}. "
            f"Retrying in {delay:.2f} seconds...")
          await asyncio.sleep(delay)
          delay *= delay_multiplier  # exponential backoff
          attempt += 1

  return json.loads(text_response)


def execute_python_function(
  code_files: dict[str, str],
  args: list,
  timeout: float,
  memory_limit: int | None,
  evaluation_script: str,
) -> str:
  """Execute a Python function in a temporary directory."""
  with tempfile.TemporaryDirectory(dir=".") as temp_dir:
    args = [f'"{arg}"' if isinstance(arg, str) else f"{arg}" for arg in args]

    # We (over)write the evaluation script in `code_files`
    with open(os.path.join(REPO_DIR, evaluation_script), encoding="utf-8") as f:
      evaluation_script_content = f.read()
      code_files[evaluation_script] = evaluation_script_content

    overlay.mirror_overlay_and_overwrite(REPO_DIR, temp_dir, code_files)

    # Run the Python program
    try:
      output = common_tools.run_command(
        ["python", evaluation_script] + args, temp_dir, timeout, memory_limit
      )
      return output
    except common_tools.FunctionExecutionError as e:
      logger.info(
        "Run command failed: %s. Attempting to read checkpoint data.", e
      )
      try:
        # If the script leaves checkpointed json data, find and return it
        output = common_tools.run_command(["cat", "checkpoint.json"], temp_dir)
        return f'{{"output": {output}, "metainfo": "Checkpoint"}}'
      except common_tools.FunctionExecutionError as ee:
        logger.info(
          "Failed to read checkpoint data: %s. Returning original error.", ee
        )
        raise common_tools.FunctionExecutionError(
          f"Execution failed: {e}"
        )


async def main_loop(
    endpoint: str,
    initial_delay: float = 1.0,
    delay_multiplier: float = 1.5,
    request_timeout: float = 30.0,
):
  response = await send_to_server(
    data={"status": "ready"},
    endpoint=endpoint,
    initial_delay=initial_delay,
    delay_multiplier=delay_multiplier,
    request_timeout=request_timeout,
  )

  while True:
    match response["action"]:
      case "stop":
        logger.info("Received stop action. Exiting.")
        break
      case "run":
        code = response.get("code")
        timeout = float(response.get("timeout"))
        memory_limit = response.get("memory_limit", None)
        if memory_limit is not None:
          memory_limit = int(memory_limit)
        args = response.get("args", ())
        evaluation_script = response.get("evaluation_script", "evaluator.py")
        try:
          result = execute_python_function(
            code, args, timeout, memory_limit, evaluation_script
          )
        except common_tools.FunctionExecutionError as e:
          logger.error("Function execution failed: %s", e)
          result = {"output": None, "metainfo": str(e)}
        except subprocess.SubprocessError as e:
          logger.error("Unexpected error: %s", e)
          if str(e) == "Exception occurred in preexec_fn.":
            result = {
              "output": None,
              "metainfo": "Execution failed: Memory limit exceeded",
            }
          else:
            result = {"output": None, "metainfo": "Internal server error"}
      case _:
        raise ValueError(f"Unknown action: {response['action']}")

    response = await send_to_server(
        data={**response, "result": result},
        endpoint=endpoint,
        initial_delay=initial_delay,
        delay_multiplier=delay_multiplier,
        request_timeout=request_timeout,
    )


# TODO: Call main_loop with a given endpoint
# if __name__ == "__main__":
  # asyncio.run(
  #   main_loop(
  #     endpoint="http://localhost:8000/api/v1/sandbox",
  #     initial_delay=1.0,
  #     delay_multiplier=1.5,
  #     request_timeout=30.0,
  #   )
  # )
