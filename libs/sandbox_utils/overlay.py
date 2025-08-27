"""Overlays a directory structure (mimics the bevaviour of mount overlayfs)."""

import os
import re
import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import Iterable, Pattern


def mirror_overlay(
  base_dir: str, overlay_dir: str, target_file_relatives: Sequence[str]
) -> None:
  """
  Mirror base_dir into overlay_dir so that:
    - Items not on the path to target_file_relative are symlinked in one go.
    - For directories on the path to target_file_relative, an actual directory
      is created in overlay_dir and its contents are symlinked, except for the
      target file.

  :param base_dir: The original directory to mirror.
  :param overlay_dir: Where to create the overlay.
  :param target_file_relatives: A list of relative paths (from base_dir) to
    files to be overridden.
  """
  # Normalize and decompose each target path into parts
  target_parts_set = set(
    tuple(rel_path.split(os.sep)) for rel_path in target_file_relatives
  )

  # Clear any existing overlay_dir.
  if os.path.exists(overlay_dir):
    shutil.rmtree(overlay_dir)
  os.makedirs(overlay_dir, exist_ok=True)

  # Process the top-level of base_dir.
  for item in os.listdir(base_dir):
    base_item = os.path.join(base_dir, item)
    overlay_item = os.path.join(overlay_dir, item)

    # Find all target paths that start with this top-level item
    sub_targets = [
      parts[1:] for parts in target_parts_set if parts and parts[0] == item
    ]

    if sub_targets:
      if os.path.isdir(base_item):
        process_target_paths(base_item, overlay_item, sub_targets)
      else:
        # File is itself a target, skip linking it
        continue
    else:
      # For items not on the target path, symlink directly.
      os.symlink(base_item, overlay_item)


def process_target_paths(
  curr_base: str, curr_overlay: str, target_parts_list: Sequence[Sequence[str]]
) -> None:
  """
  Recursively process the directory at curr_base, preserving real dirs for
    target paths.
  :param curr_base: The current base directory.
  :param curr_overlay: The corresponding overlay directory to populate.
  :param target_parts_list: A list of remaining path parts to target files under
    this subtree.
  """
  os.makedirs(curr_overlay, exist_ok=True)

  # Collect items that are on at least one target path
  items_on_target_path = set(parts[0] for parts in target_parts_list if parts)

  for item in os.listdir(curr_base):
    base_item = os.path.join(curr_base, item)
    overlay_item = os.path.join(curr_overlay, item)

    if item in items_on_target_path:
      # Get all sub-paths that continue through this item
      sub_targets = [
        parts[1:] for parts in target_parts_list if parts and parts[0] == item
      ]

      if os.path.isdir(base_item):
        process_target_paths(base_item, overlay_item, sub_targets)
      else:
        # This file is a target — skip symlinking
        continue
    else:
      os.symlink(base_item, overlay_item)


def materialize_overrides(
  overlay_dir: str, file_content_map: dict[str, str]
) -> None:
  """
  Given a map from relative file paths to content, replace the symlink at each
  path with a real file containing the specified content.

  :param overlay_dir: The root of the overlay directory.
  :param file_content_map: Dict[str, str], mapping from relative file path to
    content.
  """
  for rel_path, content in file_content_map.items():
    # Validate and sanitize the relative path
    normalized_path = os.path.normpath(rel_path)
    if normalized_path.startswith(os.sep) or ".." in normalized_path.split(
      os.sep
    ):
      raise ValueError(f"Invalid relative path detected: {rel_path}")
    full_path = os.path.join(overlay_dir, normalized_path)

    parent_dir = os.path.dirname(full_path)

    # Make sure the parent directory exists
    os.makedirs(parent_dir, exist_ok=True)

    # If a symlink exists, remove it
    if os.path.islink(full_path):
      os.unlink(full_path)

    # Write the new content
    with open(full_path, "w") as f:
      f.write(content)


def mirror_overlay_and_overwrite(
  base_dir: str,
  overlay_dir: str,
  file_content_map: dict[str, str],
) -> None:
  """
  Create an overlay of base_dir into overlay_dir, then overwrite specified files
  with content from file_content_map.

  :param base_dir: The original directory to mirror.
  :param overlay_dir: Where to create the overlay.
  :param file_content_map: Dict[str, str], mapping from relative file path to
    content to overwrite.
  """
  mirror_overlay(base_dir, overlay_dir, file_content_map.keys())
  materialize_overrides(overlay_dir, file_content_map)



def mirror_with_symlink_exceptions(
    repo_dir: str,
    dest_dir: str,
    symlink_patterns: Iterable[str] | str,
    *,
    skip_names: set[str] | None = None,
) -> None:
    """
    Copy all files/dirs from repo_dir to dest_dir, except paths that match the
    provided regex pattern(s). Those matched paths are symlinked to the source.

    - symlink_patterns: a single regex string or an iterable of regex strings,
      applied to POSIX-style *relative* paths (e.g., "sub/dir/file.py").
    - skip_names: optional set of basenames to skip entirely (e.g., {"__pycache__", ".git"}).
    """
    repo = Path(repo_dir).resolve()
    dest = Path(dest_dir).resolve()
    dest.mkdir(parents=True, exist_ok=True)

    if isinstance(symlink_patterns, str):
        combined_re: Pattern[str] = re.compile(symlink_patterns)
    else:
        combined_re = re.compile("|".join(f"(?:{p})" for p in symlink_patterns)) if symlink_patterns else re.compile(r"^\b$")  # never matches if empty

    default_skips = {"__pycache__", ".git", ".mypy_cache", ".pytest_cache", ".DS_Store"}
    if skip_names:
        default_skips |= set(skip_names)

    def rel_posix(p: Path) -> str:
        return p.relative_to(repo).as_posix()

    def should_symlink(p: Path) -> bool:
        return bool(combined_re.search(rel_posix(p)))

    def copy_file(src: Path, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        # copy2 preserves mtime/permissions where possible
        shutil.copy2(src, dst)

    def link_path(src: Path, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        # Remove pre-existing file/dir/link at destination
        if dst.exists() or dst.is_symlink():
            if dst.is_dir() and not dst.is_symlink():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        # Use absolute symlink target for robustness
        os.symlink(str(src), str(dst))

    def mirror_node(src: Path, dst: Path) -> None:
        # Skip special names
        if src.name in default_skips:
            return

        # If the *relative* path matches, symlink this node and stop
        if should_symlink(src):
            link_path(src, dst)
            return

        if src.is_symlink():
            # Preserve symlink as symlink (unless pattern says otherwise above)
            target = src.resolve()
            link_path(target, dst)
        elif src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            for child in src.iterdir():
                mirror_node(child, dst / child.name)
        elif src.is_file():
            copy_file(src, dst)
        else:
            # sockets, fifos, etc. — skip
            return

    mirror_node(repo, dest)


def apply_code_overlays(dest_dir: str, code_files: dict[str, str]) -> None:
    """
    Write overlay files into dest_dir. If a target path is a symlink,
    replace it with a regular file so we don't mutate the original repo.
    """
    dest = Path(dest_dir).resolve()
    for rel_path, content in code_files.items():
        dst = dest / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.is_symlink():
            dst.unlink()  # replace link with a file
        if dst.exists() and dst.is_dir():
            shutil.rmtree(dst)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(content)