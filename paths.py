"""Caminhos absolutos do projeto, independentes do diretório de trabalho."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
CONFIG_PATH = DATA_DIR / "config.json"
RECIPES_DIR = DATA_DIR / "recipes"
IMAGES_DIR = DATA_DIR / "images"
DB_PATH = DATA_DIR / "sp_is.db"
SIMULATION_DIR = DATA_DIR / "simulation"


def resolve_project_path(value) -> Path:
    """Resolve um caminho salvo em arquivo (relativo à raiz ou absoluto)."""
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


def to_project_relative(path) -> str:
    """Converte um caminho em caminho relativo à raiz do projeto."""
    path = Path(path).resolve()
    try:
        return path.relative_to(BASE_DIR).as_posix()
    except ValueError:
        return path.as_posix()
