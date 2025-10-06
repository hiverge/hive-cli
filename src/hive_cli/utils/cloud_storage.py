import os
from collections.abc import Sequence

from google.cloud import storage

GCR_BUCKET = "hi-artifacts"


def upload_directory(
    source_directory: str,
    list_of_files: Sequence[str],
    destination_blob_prefix: str,
    bucket_name: str = GCR_BUCKET,
) -> None:
    """
    Uploads specific files from a directory to a Cloud Storage bucket.

    Args:
        source_directory (str): Path to the local directory.
        list_of_files (List[str]): Specific files to upload, given as paths
            relative to source_directory (e.g. ["file.txt", "subdir/data.csv"]).
        destination_blob_prefix (str): Prefix for the destination blob
            names in the bucket. It can represent a "folder" in Cloud Storage.
        bucket_name (str): Name of the bucket to which files will be uploaded.
    """
    bucket = storage.Client().bucket(bucket_name)

    for relative_path in list_of_files:
        local_file_path = os.path.join(source_directory, relative_path)

        if not os.path.isfile(local_file_path):
            print(f"Skipping {relative_path} (not found)")
            continue

        # Construct blob name (use forward slashes for GCS)
        blob_name = os.path.join(
            destination_blob_prefix, relative_path
        ).replace("\\", "/")

        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_file_path)
        print(f"Uploaded {local_file_path} to gs://{bucket_name}/{blob_name}")


def parse_files_and_ranges(
    files_and_ranges: str,
) -> dict[str, tuple[int, int] | None]:
    """Parse the files and ranges from the input string.
    If a file is specified without a line range, return None as a flag to indicate omission.
    """
    file_ranges = {}
    if not files_and_ranges:
        return file_ranges

    # First handle files which we want to evolve
    for file_and_ranges in files_and_ranges.split(","):
        if ":" in file_and_ranges:
            filename, ranges = file_and_ranges.split(":")
            file_ranges[filename] = [
                tuple(map(int, r.split("-"))) for r in ranges.split("&")
            ]
        else:
            # If only filename provided, set flag for omitted range
            file_ranges[file_and_ranges] = None  # Flag for omitted range

    return file_ranges
