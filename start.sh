#!/bin/bash
# Script to setup the environment for running experiments with the Hive.

# check whether uv is installed
if ! command -v uv &> /dev/null; then
  echo "Start to install uv..."

  # Install via brew by default.
  if command -v brew &> /dev/null; then
    brew install uv
  else
    # If brew not found, use the official install script.
    curl -Ls https://astral.sh/uv/install.sh | sh
  fi

  echo "uv installed successfully."
fi

uv venv --python 3.12
source .venv/bin/activate
uv pip install -e .
uv sync --group dev
export PATH="$PROJECT/.venv/bin:$PATH"
