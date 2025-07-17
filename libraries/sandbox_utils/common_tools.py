"""Common functionality across sandboxex."""

import io
import signal
import subprocess
import threading
import time

import psutil
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


def monitor_memory(proc, limit_mb, timeout=None, check_interval=1):
  """
  Monitors a subprocess's memory usage, captures stdout and stderr,
  and kills it if it exceeds `limit_mb`. Returns (stdout, stderr, exit_code).
  """
  p = psutil.Process(proc.pid)

  stdout_lines, stderr_lines = [], []

  # Start non-blocking reading of stdout and stderr
  stdout_thread = threading.Thread(
    target=read_stream, args=(proc.stdout, stdout_lines)
  )
  stderr_thread = threading.Thread(
    target=read_stream, args=(proc.stderr, stderr_lines)
  )
  stdout_thread.start()
  stderr_thread.start()

  start_time = time.time()

  while proc.poll() is None:  # Process is still running
    try:
      mem_usage = p.memory_info().rss / (1024 * 1024)  # Convert to MB
      if mem_usage > limit_mb:
        proc.kill()
        return (
          "".join(stdout_lines),
          "".join(stderr_lines),
          -9,
        )  # Indicate forced termination
    except psutil.NoSuchProcess:
      break  # Process is already terminated

    # Check timeout
    if timeout and (time.time() - start_time) > timeout:
      print(f"Process timed out after {timeout} seconds. Killing...")
      proc.kill()
      return (
        "".join(stdout_lines),
        "".join(stderr_lines),
        -1,
      )  # Indicate timeout

    time.sleep(check_interval)  # Reduce CPU overhead

  # Ensure threads finish reading
  stdout_thread.join()
  stderr_thread.join()

  return (
    "".join(stdout_lines),
    "".join(stderr_lines),
    proc.wait(),
  )  # Return output and exit code


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
  memory_limit: int | None = None,
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
    if memory_limit:
      stdout, stderr, exit_code = monitor_memory(
        process, limit_mb=memory_limit, timeout=timeout
      )
      match exit_code:
        case -1:
          raise FunctionExecutionError("Timeout")
        case -9:
          raise FunctionExecutionError("Memory limit exceeded")
        case 0:
          return stdout
        case _:
          if exit_code < 0:
            raise FunctionExecutionError(error_code_to_string(-exit_code))
          raise FunctionExecutionError(f"Error: {stderr}")
    else:
      try:
        stdout, stderr = process.communicate(timeout=timeout)
        if process.returncode < 0:
          raise FunctionExecutionError(error_code_to_string(-exit_code))
        if process.returncode != 0:
          raise FunctionExecutionError(f"Error: {stderr}")
        return stdout
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
