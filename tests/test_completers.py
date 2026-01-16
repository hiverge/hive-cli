"""
Unit tests for argcomplete completer functions.
"""

from argparse import Namespace
from unittest.mock import MagicMock, patch

from hive_cli.completers import (
    config_file_completer,
    experiment_completer,
    sandbox_completer,
)


class TestExperimentCompleter:
    """Tests for experiment_completer function."""

    @patch("hive_cli.config.load_config")
    @patch("hive_cli.platform.k8s.K8sPlatform")
    def test_experiment_completer_success(self, mock_platform_class, mock_load_config):
        """Test experiment_completer successfully fetches and returns experiment names."""
        # Setup mock config
        mock_config = MagicMock()
        mock_config.token_path = "/path/to/token"
        mock_load_config.return_value = mock_config

        # Setup mock platform
        mock_platform = MagicMock()
        mock_platform_class.return_value = mock_platform

        # Mock K8s API response
        mock_platform.client.list_namespaced_custom_object.return_value = {
            "items": [
                {"metadata": {"name": "exp-1"}},
                {"metadata": {"name": "exp-2"}},
                {"metadata": {"name": "exp-3"}},
            ]
        }

        # Create parsed args
        parsed_args = Namespace(config=None)

        # Call completer
        result = experiment_completer("", parsed_args)

        # Verify results
        assert result == ["exp-1", "exp-2", "exp-3"]
        mock_platform.client.list_namespaced_custom_object.assert_called_once_with(
            group="core.hiverge.ai",
            version="v1alpha1",
            namespace="default",
            plural="experiments",
        )

    @patch("hive_cli.config.load_config")
    @patch("hive_cli.platform.k8s.K8sPlatform")
    def test_experiment_completer_with_prefix(self, mock_platform_class, mock_load_config):
        """Test experiment_completer filters by prefix."""
        # Setup mocks
        mock_config = MagicMock()
        mock_config.token_path = "/path/to/token"
        mock_load_config.return_value = mock_config

        mock_platform = MagicMock()
        mock_platform_class.return_value = mock_platform

        mock_platform.client.list_namespaced_custom_object.return_value = {
            "items": [
                {"metadata": {"name": "exp-1"}},
                {"metadata": {"name": "exp-2"}},
                {"metadata": {"name": "test-1"}},
            ]
        }

        parsed_args = Namespace(config=None)

        # Call completer with prefix
        result = experiment_completer("exp", parsed_args)

        # Should only return experiments starting with "exp"
        assert result == ["exp-1", "exp-2"]

    @patch("hive_cli.config.load_config")
    @patch("hive_cli.platform.k8s.K8sPlatform")
    def test_experiment_completer_k8s_error(self, mock_platform_class, mock_load_config):
        """Test experiment_completer returns empty list on K8s API error."""
        # Setup mocks
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        mock_platform = MagicMock()
        mock_platform_class.return_value = mock_platform

        # Simulate K8s API error
        mock_platform.client.list_namespaced_custom_object.side_effect = Exception("K8s error")

        parsed_args = Namespace(config=None)

        # Call completer
        result = experiment_completer("", parsed_args)

        # Should return empty list on error
        assert result == []

    @patch("hive_cli.config.load_config")
    def test_experiment_completer_config_error(self, mock_load_config):
        """Test experiment_completer returns empty list when config cannot be loaded."""
        # Simulate config loading error
        mock_load_config.side_effect = Exception("Config error")

        parsed_args = Namespace(config=None)

        # Call completer
        result = experiment_completer("", parsed_args)

        # Should return empty list on error
        assert result == []

    @patch("hive_cli.config.load_config")
    @patch("hive_cli.platform.k8s.K8sPlatform")
    def test_experiment_completer_empty_response(self, mock_platform_class, mock_load_config):
        """Test experiment_completer handles empty K8s response."""
        # Setup mocks
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        mock_platform = MagicMock()
        mock_platform_class.return_value = mock_platform

        # Mock empty response
        mock_platform.client.list_namespaced_custom_object.return_value = {"items": []}

        parsed_args = Namespace(config=None)

        # Call completer
        result = experiment_completer("", parsed_args)

        # Should return empty list
        assert result == []


class TestSandboxCompleter:
    """Tests for sandbox_completer function."""

    @patch("hive_cli.config.load_config")
    @patch("hive_cli.platform.k8s.K8sPlatform")
    def test_sandbox_completer_success(self, mock_platform_class, mock_load_config):
        """Test sandbox_completer successfully fetches and returns sandbox names."""
        # Setup mocks
        mock_config = MagicMock()
        mock_config.token_path = "/path/to/token"
        mock_load_config.return_value = mock_config

        mock_platform = MagicMock()
        mock_platform_class.return_value = mock_platform

        # Mock pods response
        mock_pod1 = MagicMock()
        mock_pod1.metadata.name = "sandbox-1"
        mock_pod2 = MagicMock()
        mock_pod2.metadata.name = "sandbox-2"

        mock_pods = MagicMock()
        mock_pods.items = [mock_pod1, mock_pod2]
        mock_platform.core_client.list_namespaced_pod.return_value = mock_pods

        parsed_args = Namespace(config=None, experiment=None)

        # Call completer
        result = sandbox_completer("", parsed_args)

        # Verify results
        assert result == ["sandbox-1", "sandbox-2"]
        mock_platform.core_client.list_namespaced_pod.assert_called_once_with(
            namespace="default",
            label_selector="app=hive-sandbox"
        )

    @patch("hive_cli.config.load_config")
    @patch("hive_cli.platform.k8s.K8sPlatform")
    def test_sandbox_completer_with_experiment_filter(self, mock_platform_class, mock_load_config):
        """Test sandbox_completer filters by experiment when provided."""
        # Setup mocks
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        mock_platform = MagicMock()
        mock_platform_class.return_value = mock_platform

        mock_pod = MagicMock()
        mock_pod.metadata.name = "sandbox-1"

        mock_pods = MagicMock()
        mock_pods.items = [mock_pod]
        mock_platform.core_client.list_namespaced_pod.return_value = mock_pods

        parsed_args = Namespace(config=None, experiment="exp-1")

        # Call completer
        result = sandbox_completer("", parsed_args)

        # Verify experiment filter was applied
        assert result == ["sandbox-1"]
        mock_platform.core_client.list_namespaced_pod.assert_called_once_with(
            namespace="default",
            label_selector="app=hive-sandbox,hiverge.ai/experiment-name=exp-1"
        )

    @patch("hive_cli.config.load_config")
    @patch("hive_cli.platform.k8s.K8sPlatform")
    def test_sandbox_completer_with_prefix(self, mock_platform_class, mock_load_config):
        """Test sandbox_completer filters by prefix."""
        # Setup mocks
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        mock_platform = MagicMock()
        mock_platform_class.return_value = mock_platform

        mock_pod1 = MagicMock()
        mock_pod1.metadata.name = "sandbox-1"
        mock_pod2 = MagicMock()
        mock_pod2.metadata.name = "sandbox-2"
        mock_pod3 = MagicMock()
        mock_pod3.metadata.name = "test-pod"

        mock_pods = MagicMock()
        mock_pods.items = [mock_pod1, mock_pod2, mock_pod3]
        mock_platform.core_client.list_namespaced_pod.return_value = mock_pods

        parsed_args = Namespace(config=None, experiment=None)

        # Call completer with prefix
        result = sandbox_completer("sandbox", parsed_args)

        # Should only return sandboxes starting with "sandbox"
        assert result == ["sandbox-1", "sandbox-2"]

    @patch("hive_cli.config.load_config")
    @patch("hive_cli.platform.k8s.K8sPlatform")
    def test_sandbox_completer_k8s_error(self, mock_platform_class, mock_load_config):
        """Test sandbox_completer returns empty list on K8s API error."""
        # Setup mocks
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config

        mock_platform = MagicMock()
        mock_platform_class.return_value = mock_platform

        # Simulate K8s API error
        mock_platform.core_client.list_namespaced_pod.side_effect = Exception("K8s error")

        parsed_args = Namespace(config=None, experiment=None)

        # Call completer
        result = sandbox_completer("", parsed_args)

        # Should return empty list on error
        assert result == []


class TestConfigFileCompleter:
    """Tests for config_file_completer function."""

    @patch("hive_cli.completers.FilesCompleter")
    def test_config_file_completer(self, mock_files_completer):
        """Test config_file_completer delegates to FilesCompleter."""
        # Setup mock
        mock_completer_instance = MagicMock()
        mock_completer_instance.return_value = ["/path/to/file1.yaml", "/path/to/file2.yaml"]
        mock_files_completer.return_value = mock_completer_instance

        parsed_args = Namespace()

        # Call completer
        result = config_file_completer("~/.hive/", parsed_args)

        # Verify FilesCompleter was used
        mock_files_completer.assert_called_once()
        assert result == ["/path/to/file1.yaml", "/path/to/file2.yaml"]
