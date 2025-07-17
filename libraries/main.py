"""A simple Python sandbox server that executes Python functions."""

import logging
import os
import subprocess
import tempfile

from flask import Flask, jsonify, request
from sandbox_utils import common_tools, overlay

REPO_DIR = "/app/repo"  # Directory where the repository is mounted

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
      try:
        # If the script leaves checkpointed json data, find and return it
        output = common_tools.run_command(["cat", "checkpoint.json"], temp_dir)
        return f'{{"output": {output}, "metainfo": "Checkpoint"}}'
      except common_tools.FunctionExecutionError:
        raise common_tools.FunctionExecutionError(
          f"Execution failed: {e}"
        ) from e


@app.route("/health", methods=["GET"])
def health_check():
  """Health check endpoint."""
  return jsonify({"status": "healthy"}), 200


@app.route("/run_code", methods=["POST"])
def run_function():
  """Run the Python function provided in the request."""
  try:
    if not request.is_json:
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

    logging.info(
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
  app.run(host="0.0.0.0", port=port)
