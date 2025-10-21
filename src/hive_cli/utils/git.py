import os
import shutil
from pathlib import Path

import git

from hive_cli.utils import time as utime
from hive_cli.utils.logger import logger


def get_codebase(source: str, dest: str, branch: str = "main") -> str:
    """
    Copy/clone repository from the given source to the destination directory.
    Args:
        source (str): The URL or path of the repository to clone.
        dest (str): The directory where the repository will be cloned.
        branch (str): The branch to checkout after cloning. Default is "main".
    Returns:
        str: The commit hash of the cloned repository.
    """
    # Case `source` is a URL, we clone it.
    if source.startswith("https://"):
        logger.debug(f"Cloning repository {source} to {dest}")

        token = os.getenv("GITHUB_TOKEN")
        if token:
            # Inject token into the URL for authentication
            source = source.replace("https://", f"https://x-access-token:{token}@")
        repo = git.Repo.clone_from(source, dest)
        repo.git.checkout(branch)
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
        if os.path.exists(os.path.join(source_path, ".git")):
            repo = git.Repo(source_path)
        else:
            # If not a repo, return a timestamp-based identifier.
            logger.warning(
                f"Source path {source} is not a git repository. Using timestamp as hash."
            )
            return utime.now_2_hash()
    try:
        code_version_id = repo.head.commit.hexsha
    except Exception as e:
        raise ValueError(f"Repository at {dest} has no commits yet: {e}") from e
    logger.debug(f"Repository copied successfully with commit ID {code_version_id}")
    return code_version_id
