"""Test `get_codebase` utility function."""

import types
from pathlib import Path

import pytest

from hive_cli.utils.git import get_codebase

HEXSHA = "deadbeef"


class _MockCommit:
    def __init__(self, hexsha):
        self.hexsha = hexsha


class _MockHead:
    def __init__(self, hexsha=HEXSHA):
        self._hexsha = hexsha

    @property
    def commit(self):
        return _MockCommit(self._hexsha)


class _MockRepo:
    def __init__(self, hexsha=HEXSHA):
        self.head = _MockHead(hexsha=hexsha)
        self.checked_out = None
        self.git = types.SimpleNamespace(
            checkout=lambda branch: setattr(self, "checked_out", branch)
        )


@pytest.fixture
def mock_git(monkeypatch):
    """
    Patch GitPython usage INSIDE the module that defines get_codebase.
    - git.Repo is replaced by a FakeRepo class
    - FakeRepo.clone_from(url, dest) returns a _MockRepo
    - Instantiating FakeRepo(path) (local path case) returns a _MockRepo
    """
    import hive_cli.utils.git as target_module  # << use the module with get_codebase

    state = {}

    class FakeRepo:
        # constructor used by: repo = git.Repo(source_path)
        def __init__(self, arg=None, *args, **kwargs):
            state["repo_arg"] = arg
            self._repo = _MockRepo()
            # delegate minimal API used by code
            self.head = self._repo.head
            self.git = self._repo.git
            self.checked_out = self._repo.checked_out

        # classmethod used by: git.Repo.clone_from(url, dest)
        @classmethod
        def clone_from(cls, url, dest, *args, **kwargs):
            state["clone_args"] = (url, dest)
            repo = _MockRepo()
            state["repo"] = repo
            return repo

    # Swap the Repo class in the git module that get_codebase imported
    monkeypatch.setattr(target_module.git, "Repo", FakeRepo, raising=True)

    return state


@pytest.fixture
def mock_copytree(monkeypatch):
    import hive_cli.utils.git as target_module

    calls = {}

    def copytree(src, dst, dirs_exist_ok=False):
        calls["args"] = (Path(src), Path(dst), dirs_exist_ok)

    monkeypatch.setattr(target_module.shutil, "copytree", copytree, raising=True)
    return calls


def test_clone_url_without_token(monkeypatch, tmp_path, mock_git):
    # No token in environment
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    url = "https://github.com/org/repo.git"
    dest = tmp_path / "dest"

    get_codebase(url, str(dest), branch="develop")

    # clone_from called with original URL (no token injected)
    called_url, called_dest = mock_git["clone_args"]
    assert called_url == url
    assert Path(called_dest) == dest

    # checkout called with the given branch
    assert mock_git["repo"].checked_out == "develop"


def test_clone_url_with_token_injected(monkeypatch, tmp_path, mock_git):
    monkeypatch.setenv("GITHUB_TOKEN", "SECRET123")

    url = "https://github.com/org/repo.git"
    dest = tmp_path / "dest"

    get_codebase(url, str(dest))

    called_url, _ = mock_git["clone_args"]
    assert called_url.startswith("https://x-access-token:SECRET123@")
    assert called_url.endswith("github.com/org/repo.git")


def test_local_path_missing(tmp_path):
    missing = tmp_path / "nope"
    with pytest.raises(FileNotFoundError) as exc:
        get_codebase(str(missing), str(tmp_path / "dest"))
    assert str(missing) in str(exc.value)


def test_local_path_not_directory(tmp_path):
    file_path = tmp_path / "somefile"
    file_path.write_text("hi")
    with pytest.raises(NotADirectoryError):
        get_codebase(str(file_path), str(tmp_path / "dest"))


def test_local_git_repo_copy(monkeypatch, tmp_path, mock_git, mock_copytree):
    # Create a real directory and a ".git" marker inside it.
    src = tmp_path / "src"
    src.mkdir()
    (src / ".git").mkdir()

    dest = tmp_path / "dest"

    get_codebase(str(src), str(dest))

    # copytree was invoked with dirs_exist_ok=True
    assert mock_copytree["args"] == (src.resolve(), dest, True)

    # git.Repo was constructed with the SOURCE path (not dest)
    assert Path(mock_git["repo_arg"]).resolve() == src.resolve()


def test_local_non_git_copy(tmp_path, mock_copytree):
    # No .git directory -> non-git path
    src = tmp_path / "src"
    src.mkdir()
    dest = tmp_path / "dest"

    get_codebase(str(src), str(dest))

    # copytree still happens
    assert mock_copytree["args"] == (src.resolve(), dest, True)
