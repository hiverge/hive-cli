"""Overlays a directory structure (mimics the bevaviour of mount overlayfs)."""

import os
import shutil
from collections.abc import Sequence


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
