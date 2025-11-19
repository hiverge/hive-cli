from hive_cli.utils import time as utime


class Runtime:
    def __init__(self, exp_name: str | None = None):
        """Initialize the Runtime with a name.
        This can be used to set up any necessary runtime configurations.
        """

        # Sometimes experiment name is not provided, e.g., for listing experiments.
        if not exp_name:
            self.experiment_name = None
        else:
            self.experiment_name = generate_experiment_name(exp_name)

        self.validate()

    def validate(self):
        if self.experiment_name and len(self.experiment_name) > 63:
            raise ValueError(
                f"experiment_name too long ({len(self.experiment_name)} chars, max 63)."
            )


def generate_experiment_name(base_name: str) -> str:
    """
    Generate a unique experiment name based on the base name and current timestamp.
    If the base name ends with '-', it will be suffixed with a timestamp.
    """

    if any(c.isupper() for c in base_name):
        raise ValueError("Experiment name must be lowercase.")

    experiment_name = base_name

    # A generated experiment name will be returned directly.
    if base_name.endswith("-"):
        hash = utime.now_2_hash()
        experiment_name = f"{base_name}{hash}"

    return experiment_name
