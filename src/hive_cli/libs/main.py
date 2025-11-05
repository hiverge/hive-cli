"""A simple Python sandbox server that executes Python functions."""

import logging
import os
import subprocess
import threading
from functools import wraps

from flask import Flask, jsonify, request

import common_tools

REPO_DIR = "/app/repo/"  # Directory where the repository is mounted
BACKUP_DIR = "/app/.backup/"  # Backup directory to restore original state

app = Flask(__name__)
sandbox_lock = threading.Lock()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def lock_sandbox():
  def decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
      if not sandbox_lock.acquire(blocking=False):
        logger.info(
          "Experiment already running on sandbox. Rejecting new request."
        )
        return jsonify(
          {"output": None, "metainfo": "Only one experiment can run at a time."}
        ), 429

      try:
        return f(*args, **kwargs)
      finally:
        sandbox_lock.release()

    return decorated_function
  return decorator


def execute_python_function(
  code_files: dict[str, str],
  args: list,
  timeout: float,
  memory_limit: int | None,
  evaluation_script: str,
) -> str:
  """Execute a Python function in a temporary directory."""
  # Restore the original repository state using rsync
  subprocess.run(["rsync", "-a", "--delete", BACKUP_DIR, REPO_DIR])

  args = [f'"{arg}"' if isinstance(arg, str) else f"{arg}" for arg in args]

  for rel_path, range_and_content in code_files.items():
    with open(os.path.join(REPO_DIR, rel_path), "w", encoding="utf-8") as f:
      f.write(range_and_content)

  # Run the Python program
  try:
    output = common_tools.run_command(
      ["python", evaluation_script] + args, REPO_DIR, timeout, memory_limit
    )
    return output
  except common_tools.FunctionExecutionError as e:
    logger.info(
      "Run command failed: %s. Attempting to read checkpoint data.", e
    )
    try:
      # If the script leaves checkpointed json data, find and return it
      output = common_tools.run_command(["cat", "checkpoint.json"], REPO_DIR)
      return f'{{"output": {output}, "metainfo": "Checkpoint"}}'
    except common_tools.FunctionExecutionError as ee:
      logger.info(
        "Failed to read checkpoint data: %s. Returning original error.", ee
      )
      raise common_tools.FunctionExecutionError(
        f"Execution failed: {e}"
      )


@app.route("/health", methods=["GET"])
def health_check():
  """Health check endpoint."""
  return jsonify({"status": "healthy"}), 200


@app.route("/run_code", methods=["POST"])
@lock_sandbox()
def run_function():
  """Run the Python function provided in the request."""
  try:
    if not request.is_json:
      logger.error("Request content type is not application/json")
      return jsonify(
        {"output": None, "metainfo": "Content-Type must be application/json"}
      ), 400

    code = request.json.get("code")
    timeout = float(request.json.get("timeout"))
    memory_limit = request.json.get("memory_limit", None)
    if memory_limit is not None:
      memory_limit = int(memory_limit)
    args = request.json.get("args", ())
    evaluation_script = request.json.get("evaluation_script", "evaluator.py")

    logger.info(
      "Executing code with timeout=%s, memory_limit=%s, evaluation_script=%s",
      timeout,
      memory_limit,
      evaluation_script,
    )

    result = execute_python_function(
      code, args, timeout, memory_limit, evaluation_script
    )
    return result, 200

  except common_tools.FunctionExecutionError as e:
    logger.error("Function execution failed: %s", e)
    return jsonify({"output": None, "metainfo": str(e)}), 400
  except subprocess.SubprocessError as e:
    logger.error("Unexpected error: %s", e)
    if str(e) == "Exception occurred in preexec_fn.":
      return jsonify(
        {"output": None, "metainfo": "Execution failed: Memory limit exceeded"}
      ), 500
    return jsonify({"output": None, "metainfo": "Internal server error"}), 500


if __name__ == "__main__":
  port = int(os.environ.get("PORT", "8080"))
  debug = os.environ.get("DEBUG", "false").lower() == "true"
  app.run(debug=debug, host="0.0.0.0", port=port)
