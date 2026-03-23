from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import settings


class DemoLoader:
    def __init__(self, demo_dir: Path | None = None) -> None:
        self.demo_dir = demo_dir or settings.demo_dir

    def load(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        papers = pd.read_csv(self.demo_dir / 'papers.csv', dtype={'pmid': str})
        entities = pd.read_csv(self.demo_dir / 'entities.csv', dtype={'pmid': str, 'entity_id': str})
        relations = pd.read_csv(self.demo_dir / 'relations.csv', dtype={'pmid': str, 'source_id': str, 'target_id': str})
        return papers, entities, relations
