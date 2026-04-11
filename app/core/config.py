from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
FLOW_FILE = DATA_DIR / "flow.json"


@dataclass
class Settings:
    project_name: str = "Flow Builder 2.0"
    static_dir: Path = STATIC_DIR
    data_dir: Path = DATA_DIR
    flow_file: Path = FLOW_FILE


settings = Settings()
