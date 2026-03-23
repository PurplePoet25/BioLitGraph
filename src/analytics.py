from __future__ import annotations

from typing import Any

import pandas as pd

from src.utils import safe_date_range


def build_timeline(papers_df: pd.DataFrame) -> list[dict[str, Any]]:
    if papers_df.empty or 'year' not in papers_df.columns:
        return []
    chunk = papers_df.dropna(subset=['year']).copy()
    if chunk.empty:
        return []
    chunk['year'] = chunk['year'].astype(int)
    grouped = chunk.groupby('year').size().reset_index(name='count').sort_values('year')
    return grouped.to_dict(orient='records')


def build_summary(
    query: str,
    source: str,
    papers_df: pd.DataFrame,
    entities_df: pd.DataFrame,
    graph_payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        'query': query,
        'source': source,
        'paper_count': int(len(papers_df)),
        'entity_mentions': int(len(entities_df)),
        'unique_entities': int(len(graph_payload.get('graph', {}).get('nodes', []))),
        'edge_count': int(len(graph_payload.get('graph', {}).get('edges', []))),
        'date_range': safe_date_range(papers_df.get('year', [])),
    }
