import pytest

from hive_cli.runtime.runtime import Runtime


def test_generate_experiment_name():
    runtime0 = Runtime()
    assert runtime0.experiment_name is None

    runtime1 = Runtime("test-experiment")
    assert runtime1.experiment_name == "test-experiment"

    runtime2 = Runtime("experiment-")
    assert runtime2.experiment_name.startswith("experiment-")

    with pytest.raises(ValueError):
        Runtime("InvalidName")  # Uppercase letters should raise ValueError
