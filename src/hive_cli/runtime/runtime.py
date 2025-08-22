import hashlib
from datetime import datetime, timezone


class Runtime:
    def __init__(self, name: str, token_path: str = None):
        """Initialize the Runtime with a name.
        This can be used to set up any necessary runtime configurations.
        """

        self.token_path = token_path
        self.experiment_name = generate_experiment_name(name)


def generate_experiment_name(base_name: str) -> str:
    """
    Generate a unique experiment name based on the base name and current timestamp.
    If the base name ends with '-', it will be suffixed with a timestamp.
    """

    experiment_name = base_name

    if base_name.endswith("-"):
        timestamp = str(int(datetime.now(timezone.utc).timestamp()))
        unique_hash = hashlib.sha1(timestamp.encode()).hexdigest()[:7]
        experiment_name = f"{base_name}{unique_hash}"

    return experiment_name
