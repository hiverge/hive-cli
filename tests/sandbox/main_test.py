"""Tests for the executor module."""

import os
import unittest
from unittest import mock
import importlib
import asyncio

import time

import libs.main


class LockTest(unittest.IsolatedAsyncioTestCase):
  """Tests for the lock mechanism."""

  async def test_lock_sandbox(self):
    """Tests that the sandbox lock works correctly."""
    with mock.patch.dict(os.environ, {"LOCK_SANDBOX": "true"}):
      # Reload module so that locking variable is set
      importlib.reload(libs.main)

      # We will mock `execute_python_function` so it just sleeps for a second
      def _sleep_and_execute(*args, **kwargs):
        time.sleep(1.0)
        return '{"output": "success", "metainfo": ""}'

      with mock.patch.object(
        libs.main, "execute_python_function", _sleep_and_execute,
      ):
        # Setup mock server response
        app = libs.main.app.test_client()
        
        async def _post_request():
          """Run a synchronous Flask test client request in a thread."""
          payload = {"code": {"": ""}, "timeout": 10, "args": []}
          return await asyncio.to_thread(app.post, "/run_code", json=payload)

        # Send two requests to the sandbox and check that one works and one 
        # fails
        responses = await asyncio.gather(_post_request(), _post_request())
        codes = {resp.status_code for resp in responses}
        self.assertEqual(codes, {200, 429})

        # Check that sandbox has unlocked properly
        response = await _post_request()
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
  unittest.main()
