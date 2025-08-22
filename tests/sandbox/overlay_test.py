"""Test the overlay creation logic."""

import os
import shutil
import tempfile
import unittest

from libs.sandbox_utils import overlay


class TestMirrorOverlay(unittest.TestCase):
  """Unit test for the overlay logic."""

  def setUp(self):
    # Setup a base directory with the following structure:
    # base_directory/
    # ├─ a.txt
    # ├─ b.txt
    # ├─ subdir/
    # │  ├─ c.txt
    # │  ├─ d.txt
    # ├─ sub1/
    # │  ├─ another.txt
    # │  ├─ sub2/
    # │  │  ├─ other.txt
    # │  │  ├─ subling.txt
    # │  │  ├─ target.txt     <- This is the target file
    # Create temporary directories for the base and overlay.
    self.base_dir = tempfile.mkdtemp(prefix="base_")
    # We'll let mirror_overlay recreate overlay_dir, so just define its path.
    self.overlay_dir = os.path.join(tempfile.gettempdir(), "overlay_test")

    # Build a sample directory structure in base_dir.
    # Create some files at the root.
    with open(os.path.join(self.base_dir, "a.txt"), "w", encoding="utf-8") as f:
      f.write("Content of a.txt")
    with open(os.path.join(self.base_dir, "b.txt"), "w", encoding="utf-8") as f:
      f.write("Content of b.txt")

    # Create a directory "subdir" with files.
    os.makedirs(os.path.join(self.base_dir, "subdir"))
    with open(
      os.path.join(self.base_dir, "subdir", "c.txt"), "w", encoding="utf-8"
    ) as f:
      f.write("Content of c.txt")
    with open(
      os.path.join(self.base_dir, "subdir", "d.txt"), "w", encoding="utf-8"
    ) as f:
      f.write("Content of d.txt")

    # Create the nested directory "sub1/sub2".
    os.makedirs(os.path.join(self.base_dir, "sub1", "sub2"))
    # Create the target file.
    with open(
      os.path.join(self.base_dir, "sub1", "sub2", "target.txt"),
      "w",
      encoding="utf-8",
    ) as f:
      f.write("Original target content")
    # Create sibling files in the same directory as the target file.
    with open(
      os.path.join(self.base_dir, "sub1", "sub2", "other.txt"),
      "w",
      encoding="utf-8",
    ) as f:
      f.write("Content of other.txt")
    with open(
      os.path.join(self.base_dir, "sub1", "sub2", "sibling.txt"),
      "w",
      encoding="utf-8",
    ) as f:
      f.write("Content of sibling.txt")
    # Create another file in sub1 (outside the sub2 directory).
    with open(
      os.path.join(self.base_dir, "sub1", "another.txt"), "w", encoding="utf-8"
    ) as f:
      f.write("Content of another.txt")

  def tearDown(self):
    shutil.rmtree(self.base_dir)
    if os.path.exists(self.overlay_dir):
      shutil.rmtree(self.overlay_dir)

  def test_mirror_overlay_one_target(self):
    """Test the overlay creation logic."""

    # Execute the overlay creation.
    overlay.mirror_overlay(
      self.base_dir,
      self.overlay_dir,
      [os.path.join("sub1", "sub2", "target.txt")],
    )

    # Files at the root of overlay_dir should be symlinks.
    a_link = os.path.join(self.overlay_dir, "a.txt")
    b_link = os.path.join(self.overlay_dir, "b.txt")
    self.assertTrue(os.path.islink(a_link), "a.txt should be a symlink.")
    self.assertTrue(os.path.islink(b_link), "b.txt should be a symlink.")

    # "subdir" should be entirely symlinked.
    subdir_link = os.path.join(self.overlay_dir, "subdir")
    self.assertTrue(os.path.islink(subdir_link), "subdir should be a symlink.")

    # "sub1" should be a real directory since it's on the path to the target.
    sub1_dir = os.path.join(self.overlay_dir, "sub1")
    self.assertFalse(
      os.path.islink(sub1_dir), "sub1 should be a real directory."
    )
    self.assertTrue(
      os.path.isdir(sub1_dir), "sub1 should exist as a directory."
    )

    # In "sub1", "another.txt" should be symlinked.
    another_link = os.path.join(sub1_dir, "another.txt")
    self.assertTrue(
      os.path.islink(another_link), "another.txt in sub1 should be a symlink."
    )

    # "sub1/sub2" should be a real directory.
    sub2_dir = os.path.join(sub1_dir, "sub2")
    self.assertFalse(
      os.path.islink(sub2_dir), "sub1/sub2 should be a real directory."
    )
    self.assertTrue(
      os.path.isdir(sub2_dir), "sub1/sub2 should exist as a directory."
    )

    # In "sub1/sub2":
    # - "target.txt" should NOT exist (it is the file to be overridden).
    target_path = os.path.join(sub2_dir, "target.txt")
    self.assertFalse(
      os.path.exists(target_path),
      "target.txt should be absent from the overlay.",
    )

    # - All other files should be symlinked.
    other_link = os.path.join(sub2_dir, "other.txt")
    sibling_link = os.path.join(sub2_dir, "sibling.txt")
    self.assertTrue(
      os.path.islink(other_link), "other.txt should be a symlink in sub1/sub2."
    )
    self.assertTrue(
      os.path.islink(sibling_link),
      "sibling.txt should be a symlink in sub1/sub2.",
    )

  def test_mirror_overlay_multiple_targets(self):
    """Test the overlay creation with multiple target files."""
    # Add another target file.
    overlay.mirror_overlay(
      self.base_dir,
      self.overlay_dir,
      [
        os.path.join("sub1", "sub2", "other.txt"),
        os.path.join("subdir", "c.txt"),
      ],
    )

    # Check that "d.txt" in "subdir" is symlinked.
    d_link = os.path.join(self.overlay_dir, "subdir", "d.txt")
    self.assertTrue(os.path.islink(d_link), "subdir/d.txt should be a symlink.")
    # Check that "sub1/another.txt" is symlinked.
    another_link = os.path.join(self.overlay_dir, "sub1", "another.txt")
    self.assertTrue(
      os.path.islink(another_link), "sub1/another.txt should be a symlink."
    )
    # Check that "sub1/sub2/other.txt" is still not present.
    other_target_path = os.path.join(
      self.overlay_dir, "sub1", "sub2", "other.txt"
    )
    self.assertFalse(
      os.path.exists(other_target_path),
      "sub1/sub2/other.txt should not exist in the overlay.",
    )
    # Check that "subdir/c.txt" is still not present.
    c_target_path = os.path.join(self.overlay_dir, "subdir", "c.txt")
    self.assertFalse(
      os.path.exists(c_target_path),
      "subdir/c.txt should not exist in the overlay.",
    )

  def test_mirror_overlay_no_targets(self):
    """Test the overlay creation with no target files."""
    # Execute the overlay creation with no targets.
    overlay.mirror_overlay(self.base_dir, self.overlay_dir, [])

    # All files in the base directory should be symlinked in the overlay.
    a_link = os.path.join(self.overlay_dir, "a.txt")
    b_link = os.path.join(self.overlay_dir, "b.txt")
    self.assertTrue(os.path.islink(a_link), "a.txt should be a symlink.")
    self.assertTrue(os.path.islink(b_link), "b.txt should be a symlink.")

    # The "subdir" directory should be symlinked.
    subdir_link = os.path.join(self.overlay_dir, "subdir")
    self.assertTrue(os.path.islink(subdir_link), "subdir should be a symlink.")

    # The "sub1" directory should be symlinked.
    sub1_link = os.path.join(self.overlay_dir, "sub1")
    self.assertTrue(os.path.islink(sub1_link), "sub1 should be a symlink.")

  def test_mirror_overlay_and_overwrite(self):
    """Test the overlay creation and file content overwriting."""
    # Define the content to overwrite the target file.
    file_content_map = {
      "sub1/sub2/target.txt": "Overwritten target content",
      "subdir/c.txt": "Overwritten c.txt content",
    }

    # Execute the overlay creation and overwrite.
    overlay.mirror_overlay_and_overwrite(
      self.base_dir, self.overlay_dir, file_content_map
    )

    # Check that the target file has been overwritten.
    target_path = os.path.join(self.overlay_dir, "sub1", "sub2", "target.txt")
    self.assertTrue(
      os.path.exists(target_path), "target.txt should exist in the overlay."
    )
    with open(target_path, encoding="utf-8") as f:
      content = f.read()
      self.assertEqual(
        content,
        "Overwritten target content",
        "Content of target.txt is incorrect.",
      )

    # Check that c.txt has been overwritten.
    c_target_path = os.path.join(self.overlay_dir, "subdir", "c.txt")
    self.assertTrue(
      os.path.exists(c_target_path), "subdir/c.txt should exist in the overlay."
    )
    with open(c_target_path, encoding="utf-8") as f:
      content = f.read()
      self.assertEqual(
        content,
        "Overwritten c.txt content",
        "Content of subdir/c.txt is incorrect.",
      )

  def test_mirror_overlay_and_overwrite_exception(self):
    """Test the exception raised when the file path is invalid."""
    with tempfile.TemporaryDirectory() as temp_dir:
      overlay_dir = os.path.join(temp_dir, "overlay_test")
      base_dir = os.path.join(temp_dir, "base_test")
      os.makedirs(base_dir, exist_ok=True)

      # Define an invalid relative path
      file_content_map = {"../invalid_path.txt": "This should raise an error"}

      with self.assertRaises(
        ValueError, msg="Invalid relative path detected: ../invalid_path.txt"
      ):
        overlay.mirror_overlay_and_overwrite(
          base_dir, overlay_dir, file_content_map
        )


if __name__ == "__main__":
  unittest.main()
