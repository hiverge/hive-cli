"""Common functionality across sandboxex."""

import io
import signal
import subprocess
import time

import requests

GCR_SANDBOX_BUCKET = "hi-sandbox"


def read_stream(stream, output_list):
  """Helper function to read stream line by line and store it in a list."""
  try:
    for line in iter(stream.readline, ""):
      output_list.append(line)
  except (io.UnsupportedOperation, UnicodeDecodeError) as e:
    output_list.append(f"[Error reading stream] {e}")
  finally:
    stream.close()

class FunctionExecutionError(Exception):
  """Exception raised when a function execution fails."""


def error_code_to_string(sig: int) -> str:
  """Convert a signal code to a string."""
  sig_name = signal.Signals(sig).name
  sig_desc = signal.strsignal(sig)
  return f"Terminated by signal {sig} ({sig_name}): {sig_desc}"


def run_command(
  cmd: str,
  cwd: str = ".",
  timeout: float = 10.0,
) -> str:
  """Run a command with timeout and return the output."""

  with subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    cwd=cwd,
    bufsize=1,  # Allows real-time output
    universal_newlines=True,
    text=True,
  ) as process:
    try:
      stdout, stderr = process.communicate(timeout=timeout)
      if process.returncode < 0:
        raise FunctionExecutionError(error_code_to_string(-process.returncode))
      if process.returncode != 0:
        raise FunctionExecutionError(f"Error: {stderr}")
      return stdout.strip().splitlines()[-1]  # Return only the last line of output
    except subprocess.TimeoutExpired as exc:
      process.kill()
      raise FunctionExecutionError("Timeout") from exc


def wait_for_url(url: str, timeout: int = 300, interval: int = 1) -> bool:
  """
  Keep checking a URL until it returns a response or timeout is reached.

  Args:
      url (str): The URL to check.
      timeout (int): Total time to keep trying (in seconds).
      interval (int): Time to wait between retries (in seconds).

  Returns:
      bool: True if `url` is available.
  """
  start_time = time.time()

  while time.time() - start_time < timeout:
    try:
      response = requests.get(url)
      if response.status_code == 200:
        return True
    except requests.RequestException:
      # Optionally log the exception or just continue
      pass
    print(f"Waiting for {url} to be available...")
    time.sleep(interval)

  return False


def stop_and_remove_image(image_name: str):
  """Stop and remove a Docker image."""

  # Step 1: Find running container for the image
  containers = (
    subprocess.check_output(
      ["docker", "ps", "-q", "--filter", f"ancestor={image_name}"]
    )
    .decode()
    .strip()
    .splitlines()
  )

  for container_id in containers:
    # Step 2: Stop the container
    subprocess.run(
      ["docker", "stop", container_id],
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
      check=False,
    )
    # Step 3: Remove the container
    subprocess.run(
      ["docker", "rm", container_id],
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
      check=False,
    )

  # Step 4: Remove the image in the background
  subprocess.Popen(
    ["docker", "rmi", image_name],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
  )
