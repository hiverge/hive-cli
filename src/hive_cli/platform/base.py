from abc import ABC, abstractmethod

from datetime import datetime

class Platform(ABC):
    @abstractmethod
    def init(self, args):
        pass

    @abstractmethod
    def create(self, args):
        pass

    @abstractmethod
    def delete(self, args):
        pass

    @abstractmethod
    def login(self, args):
        pass

    @abstractmethod
    def show_experiments(self, args):
        pass


    def generate_experiment_name(self, base_name: str) -> str:
        """
        Generate a unique experiment name based on the base name and current timestamp.
        If the base name ends with '-', it will be suffixed with a timestamp.
        """
        if base_name.endswith('-'):
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            return f"{base_name}{timestamp}"
        return base_name
