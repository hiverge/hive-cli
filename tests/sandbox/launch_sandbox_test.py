"""Tests for launch_sandbox focusing on the local deployment."""

# TODO: Reimplement these tests
# import os
# import unittest

# import requests
# from libs.sandbox_utils import common_tools, launch_sandbox

# CODE = """
# def hive_main():
#     return {'message': 'Hello, World!'}
# """

# URL = "http://localhost:8080"


# class TestLaunchSandbox(unittest.TestCase):
#   """Tests for the launch_sandbox function."""

#   def test_launch_sandbox_local(self):
#     """Test launching the sandbox locally."""

#     cwd = launch_sandbox.get_relative_path()
#     dockerfile_path = os.path.join("python_sandbox_server", "Dockerfile")
#     # Assuming the function returns a URL, we can check if it starts with "http"
#     url = launch_sandbox.launch_sandbox(
#       dockerfile_path=dockerfile_path,
#       project_id="test-project",
#       sandbox_name="test-sandbox",
#       deploy_optional_args={},
#       where_to_deploy="local",
#       relative_path=cwd,
#     )
#     self.assertEqual(url, URL)

#     # Send a request to the local server to check if it's running
#     response = requests.get(f"{URL}/health")
#     self.assertEqual(response.status_code, 200)
#     self.assertEqual(response.json(), {"status": "healthy"})

#     # Use the sandbox
#     response = requests.post(
#       f"{URL}/run",
#       json={"code": CODE, "timeout": 10},
#     )

#     self.assertEqual(response.status_code, 200)
#     self.assertEqual(response.json()["output"], {"message": "Hello, World!"})
#     common_tools.stop_and_remove_image("test-project/test-sandbox")
