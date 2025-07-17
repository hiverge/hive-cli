from pathlib import Path
import tempfile

import yaml

from hive_cli.config import HiveConfig
from .base import Platform

class K8sPlatform(Platform):
    def create(self, name: str, config: HiveConfig):
        print(f"Creating experiment on Kubernetes with name: {self.generate_experiment_name(name)}")

        with tempfile.TemporaryDirectory(dir="./tmp") as temp_dir:
            # create a a.txt file in the temporary directory
            with open(Path(temp_dir) / "a.txt", "w") as f:
                f.write("This is a temporary file for testing.")


    def delete(self, args):
        print("Deleting experiment on Kubernetes...")

    def login(self, args):
        print("Logging in to hive on Kubernetes...")

    def show_experiments(self, args):
        print("Showing experiments on Kubernetes...")

def generate_dockerfile(dest: Path) -> None:
  """Create a Dockerfile inside `dest`."""
  lines = [
    "FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim",
    "",
    "RUN apt-get update && apt-get install --no-install-recommends -y \\",
    "cmake \\",
    "build-essential \\",
    "pkg-config \\",
    "&& rm -rf /var/lib/apt/lists/*",
    "",
    "WORKDIR /app",
    "",
    "# Install sandbox server dependencies",
  ]
  if (dest / "pyproject.toml").exists():
    lines.append("# Install repository dependencies from pyproject.toml")
    lines.append("COPY pyproject.toml .")
    lines.append("RUN uv pip install --system --requirement pyproject.toml")
  elif (dest / "requirements.txt").exists():
    lines.append("# Install repository dependencies from requirements.txt")
    lines.append("COPY requirements.txt .")
    lines.append("RUN uv pip install --system --requirement requirements.txt")

  lines.extend(
    [
      "",
      "# Copy server code and evaluation file",
      "COPY . repo",
    ]
  )
  (dest / "Dockerfile").write_text("\n".join(lines), encoding="utf-8")
