import hashlib
from datetime import datetime, timezone


class Runtime:
    def __init__(self, exp_name: str | None, token_path: str = None):
        """Initialize the Runtime with a name.
        This can be used to set up any necessary runtime configurations.
        """

        # Sometimes experiment name is not provided, e.g., for listing experiments.
        if not exp_name:
            self.experiment_name = None
        else:
            self.experiment_name = generate_experiment_name(exp_name)


def generate_experiment_name(base_name: str) -> str:
    """
    Generate a unique experiment name based on the base name and current timestamp.
    If the base name ends with '-', it will be suffixed with a timestamp.
    """

    experiment_name = base_name

    # A generated experiment name will be returned directly.
    if base_name.endswith("-"):
        timestamp = str(int(datetime.now(timezone.utc).timestamp()))
        unique_hash = hashlib.sha1(timestamp.encode()).hexdigest()[:7]
        experiment_name = f"{base_name}{unique_hash}"

    return experiment_name
