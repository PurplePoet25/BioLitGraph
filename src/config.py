
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _resource_base_dir() -> Path:
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def _user_data_dir(app_name: str = 'BioLitGraph') -> Path:
    override = os.getenv('BIOLITGRAPH_HOME', '').strip()
    if override:
        return Path(override).expanduser().resolve()

    if sys.platform.startswith('win'):
        base = os.getenv('LOCALAPPDATA')
        if base:
            return Path(base) / app_name
        return Path.home() / 'AppData' / 'Local' / app_name

    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / app_name

    xdg = os.getenv('XDG_DATA_HOME')
    if xdg:
        return Path(xdg) / app_name
    return Path.home() / '.local' / 'share' / app_name


BASE_DIR = _resource_base_dir()
USER_DATA_DIR = _user_data_dir()


@dataclass(frozen=True)
class Settings:
    base_dir: Path = BASE_DIR
    user_data_dir: Path = USER_DATA_DIR
    data_dir: Path = BASE_DIR / 'data'
    demo_dir: Path = BASE_DIR / 'data' / 'demo'
    outputs_dir: Path = USER_DATA_DIR / 'outputs'
    runs_dir: Path = USER_DATA_DIR / 'outputs' / 'runs'
    raw_dir: Path = USER_DATA_DIR / 'data' / 'raw'
    interim_dir: Path = USER_DATA_DIR / 'data' / 'interim'
    processed_dir: Path = USER_DATA_DIR / 'data' / 'processed'
    ncbi_base_url: str = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils'
    pubtator_base_url: str = 'https://www.ncbi.nlm.nih.gov/research/pubtator3-api'
    ncbi_tool: str = os.getenv('NCBI_TOOL', 'BioLitGraph')
    ncbi_email: str = os.getenv('NCBI_EMAIL', 'your_email@example.com')
    ncbi_api_key: str = os.getenv('NCBI_API_KEY', '')
    request_timeout: int = int(os.getenv('REQUEST_TIMEOUT', '30'))

    @property
    def ncbi_requests_per_second(self) -> float:
        return 9.0 if self.ncbi_api_key else 2.8


settings = Settings()

for path in [
    settings.demo_dir,
    settings.outputs_dir,
    settings.runs_dir,
    settings.raw_dir,
    settings.interim_dir,
    settings.processed_dir,
]:
    path.mkdir(parents=True, exist_ok=True)
