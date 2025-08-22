import os
import shutil
from pathlib import Path

import git


def clone_repo(repo_dir: str, output_dir: str, branch: str = "main") -> str:
    """Clone a repository into the output directory."""
    dest = Path(output_dir)
    dest.mkdir(parents=True, exist_ok=True)
    if repo_dir.startswith("https://"):
        token = os.getenv("GITHUB_TOKEN")
        if token:
            # Inject token into the URL for authentication
            repo_dir = repo_dir.replace("https://", f"https://x-access-token:{token}@")
        repo = git.Repo.clone_from(repo_dir, dest)
        repo.git.checkout(branch)
    else:  # We assume `repo_dir` is a directory in this machine.
        repo_path = Path(repo_dir).resolve()
        if not repo_path.exists():
            raise FileNotFoundError(f"Repository directory {repo_dir} does not exist")
        if not repo_path.is_dir():
            raise NotADirectoryError(f"{repo_dir} is not a directory")
        shutil.copytree(repo_path, dest, dirs_exist_ok=True)
        repo = git.Repo(dest)

    return repo.head.commit.hexsha
