import os
import random
import shutil
import string
from pathlib import Path

import git

from hive_cli.utils.logger import logger


def clone_repo(repo_dir: str, output_dir: str, branch: str = "main") -> str:
    """Clone a repository into the output directory."""
    dest = Path(output_dir)
    dest.mkdir(parents=True, exist_ok=True)
    if repo_dir.startswith("https://"):
        token = os.getenv("GITHUB_TOKEN")
        if token:
            # Inject token into the URL for authentication
            repo_dir = repo_dir.replace(
                "https://", f"https://x-access-token:{token}@"
            )
        repo = git.Repo.clone_from(repo_dir, dest)
        repo.git.checkout(branch)
    else:  # We assume `repo_dir` is a directory in this machine.
        repo_path = Path(repo_dir).resolve()
        if not repo_path.exists():
            raise FileNotFoundError(
                f"Repository directory {repo_dir} does not exist"
            )
        if not repo_path.is_dir():
            raise NotADirectoryError(f"{repo_dir} is not a directory")
        shutil.copytree(repo_path, dest, dirs_exist_ok=True)
        repo = git.Repo(dest)

    return repo.head.commit.hexsha


def get_codebase(source: str, dest: str, branch: str = "main") -> str:
    """
    Copy/clone repository from the given source to the destination directory.

    Args:
        source (str): The URL or path of the repository to clone.
        dest (str): The destination directory where the repository will be cloned.
        branch (str): The branch to checkout after cloning. Default is "main".

    Returns:
        str: The commit hash of the cloned repository.
    """
    # Case `source` is a URL, we clone it.
    if source.startswith("https://"):
        logger.debug(f"Cloning repository {source} to {dest}")
        code_version_id = clone_repo(source, dest, branch)
        logger.debug(
            f"Repository cloned successfully with commit ID {code_version_id}"
        )
        return code_version_id[:7]
    else:
        # Case `source` is a local path, we copy it.
        source_path = Path(source).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Source path {source} does not exist")
        if not source_path.is_dir():
            raise NotADirectoryError(f"Source path {source} is not a directory")

        logger.debug(f"Copying repository from {source} to {dest}")
        shutil.copytree(source_path, dest, dirs_exist_ok=True)

        # Get the current commit hash if it's a git repository.
        if (source_path / ".git").exists():
            repo = git.Repo(source_path)
            code_version_id = repo.head.commit.hexsha
            logger.debug(
                f"Repository copied successfully with commit ID {code_version_id}"
            )
            return code_version_id
        else:
            logger.warning(
                f"Source path {source} is not a git repository. "
                f"Using a random string as commit ID."
            )
            return "".join(
                random.choices(string.ascii_lowercase + string.digits, k=7)
            )
