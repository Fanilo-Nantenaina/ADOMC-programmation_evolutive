import os
import pickle

DEFAULT_MODEL_DIR = "models"
DEFAULT_FILENAME = "portfolio_policy.pkl"


class PolicyManager:
    """Sauvegarde / chargement des génomes NEAT + métadonnées d'entraînement."""

    def __init__(self, save_dir: str = DEFAULT_MODEL_DIR):
        self.save_dir = save_dir
        os.makedirs(self.save_dir, exist_ok=True)

    def _path(self, filename: str) -> str:
        return os.path.join(self.save_dir, filename)

    def save(self, genome, metadata: dict, filename: str = DEFAULT_FILENAME) -> str:

        path = self._path(filename)
        bundle = {"genome": genome, "metadata": dict(metadata)}
        with open(path, "wb") as f:
            pickle.dump(bundle, f)
        return path

    def load(self, filename: str = DEFAULT_FILENAME):
        """Retourne le bundle ou None si absent / corrompu."""
        path = self._path(filename)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except (pickle.UnpicklingError, EOFError, AttributeError):
            return None

    def exists(self, filename: str = DEFAULT_FILENAME) -> bool:
        return os.path.exists(self._path(filename))

    def delete(self, filename: str = DEFAULT_FILENAME) -> bool:
        path = self._path(filename)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
