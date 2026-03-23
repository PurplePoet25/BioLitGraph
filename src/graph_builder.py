from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Any

import networkx as nx
import pandas as pd

from src.utils import choose_display_label, humanize_relation_label


class GraphBuilder:
    GENERIC_LABELS_BY_TYPE = {
        'Disease': {
            'cancer', 'tumor', 'tumors', 'malignancy', 'malignancies', 'infection', 'infections',
            'disease', 'diseases', 'disorder', 'disorders', 'loss', 'cyst', 'cysts',
        },
        'Chemical': {'water', 'salt'},
    }
    GENERIC_NORMALIZED_IDS = {
        'MESH:D009369',  # generic cancer/tumor bucket
        'MESH:D007239',  # generic infection bucket
    }

    def __init__(self, min_node_support: int = 2, min_edge_support: int = 2) -> None:
        self.min_node_support = min_node_support
        self.min_edge_support = min_edge_support

    def build(
        self,
        papers_df: pd.DataFrame,
        entities_df: pd.DataFrame,
        relations_df: pd.DataFrame | None = None,
    ) -> dict[str, Any]:
        if entities_df.empty:
            return self._empty_payload()

        nodes_df = self._aggregate_nodes(entities_df)
        diagnostics = {
            'raw_node_count': int(len(nodes_df)),
            'generic_nodes_removed': 0,
            'isolated_nodes_removed': 0,
        }

        filtered_nodes_df = nodes_df.loc[nodes_df['support_count'] >= self.min_node_support].copy()
        filtered_nodes_df, generic_removed = self._drop_generic_nodes(filtered_nodes_df)
        diagnostics['generic_nodes_removed'] = int(generic_removed)

        kept_nodes = set(filtered_nodes_df['entity_id'])
        filtered_mentions = entities_df.loc[entities_df['entity_id'].isin(kept_nodes)].copy()

        cooccurrence_edges = self._build_cooccurrence_edges(filtered_mentions)
        if relations_df is not None and not relations_df.empty:
            relation_edges = self._build_relation_edges(relations_df, kept_nodes)
            edges_df = self._merge_edges(cooccurrence_edges, relation_edges)
        else:
            edges_df = cooccurrence_edges

        if not edges_df.empty:
            edges_df = edges_df.loc[edges_df['support_count'] >= self.min_edge_support].copy()
        else:
            edges_df = pd.DataFrame(columns=['source_id', 'target_id', 'edge_kind', 'relation_label', 'support_count', 'pmids'])

        if not edges_df.empty:
            edge_nodes = set(edges_df['source_id']).union(set(edges_df['target_id']))
            isolated_removed = len(filtered_nodes_df) - int(filtered_nodes_df['entity_id'].isin(edge_nodes).sum())
            diagnostics['isolated_nodes_removed'] = max(int(isolated_removed), 0)
            filtered_nodes_df = filtered_nodes_df.loc[filtered_nodes_df['entity_id'].isin(edge_nodes)].copy()
            kept_nodes = set(filtered_nodes_df['entity_id'])
            edges_df = edges_df.loc[edges_df['source_id'].isin(kept_nodes) & edges_df['target_id'].isin(kept_nodes)].copy()

        if filtered_nodes_df.empty:
            payload = self._empty_payload()
            payload['diagnostics'] = diagnostics | {
                'final_node_count': 0,
                'final_edge_count': 0,
                'signal': 'low',
            }
            return payload

        graph = nx.Graph()
        node_lookup = filtered_nodes_df.set_index('entity_id').to_dict(orient='index')

        for _, row in filtered_nodes_df.iterrows():
            graph.add_node(
                row['entity_id'],
                label=row['label'],
                entity_type=row['entity_type'],
                support_count=int(row['support_count']),
                normalized_id=row['normalized_id'],
                aliases=row['aliases'],
            )

        for _, row in edges_df.iterrows():
            if row['source_id'] not in kept_nodes or row['target_id'] not in kept_nodes:
                continue
            graph.add_edge(
                row['source_id'],
                row['target_id'],
                support_count=int(row['support_count']),
                edge_kind=row['edge_kind'],
                relation_label=row['relation_label'],
                pmids=row['pmids'],
            )

        node_details: dict[str, Any] = {}
        edge_details: dict[str, Any] = {}
        graph_nodes: list[dict[str, Any]] = []
        graph_edges: list[dict[str, Any]] = []
        paper_lookup = papers_df.set_index('pmid').to_dict(orient='index') if not papers_df.empty else {}

        for node_id, attrs in graph.nodes(data=True):
            neighbors = []
            for neighbor in graph.neighbors(node_id):
                neighbor_attrs = graph.nodes[neighbor]
                support = graph.edges[node_id, neighbor]['support_count']
                neighbors.append(
                    {
                        'entity_id': neighbor,
                        'label': neighbor_attrs.get('label', neighbor),
                        'entity_type': neighbor_attrs.get('entity_type', 'Unknown'),
                        'support_count': support,
                    }
                )
            neighbors.sort(key=lambda item: (-item['support_count'], item['label']))
            connected_pmids = sorted({pmid for edge in graph.edges(node_id, data=True) for pmid in edge[2].get('pmids', [])})
            supporting_papers = [self._paper_card(pmid, paper_lookup) for pmid in connected_pmids[:15]]
            detail = {
                'label': attrs.get('label', node_id),
                'entity_type': attrs.get('entity_type', 'Unknown'),
                'normalized_id': attrs.get('normalized_id', node_id),
                'support_count': attrs.get('support_count', 0),
                'degree': graph.degree(node_id),
                'aliases': attrs.get('aliases', []),
                'neighbors': neighbors[:10],
                'papers': supporting_papers,
            }
            node_details[node_id] = detail
            graph_nodes.append(
                {
                    'id': node_id,
                    'label': attrs.get('label', node_id),
                    'group': attrs.get('entity_type', 'Unknown'),
                    'value': int(attrs.get('support_count', 1)),
                    'title': f"{attrs.get('label', node_id)} ({attrs.get('entity_type', 'Unknown')})<br>Seen in {attrs.get('support_count', 0)} papers",
                }
            )

        for idx, (source, target, attrs) in enumerate(graph.edges(data=True), start=1):
            edge_id = f'edge-{idx}'
            relation_label = humanize_relation_label(attrs.get('relation_label', ''), attrs.get('edge_kind', ''))
            papers = [self._paper_card(pmid, paper_lookup) for pmid in attrs.get('pmids', [])[:20]]
            edge_details[edge_id] = {
                'source': graph.nodes[source].get('label', source),
                'target': graph.nodes[target].get('label', target),
                'edge_kind': attrs.get('edge_kind', 'cooccurrence'),
                'relation_label': relation_label,
                'support_count': attrs.get('support_count', 0),
                'papers': papers,
            }
            graph_edges.append(
                {
                    'id': edge_id,
                    'from': source,
                    'to': target,
                    'value': int(attrs.get('support_count', 1)),
                    'label': str(attrs.get('support_count', 1)),
                    'title': f"{graph.nodes[source].get('label', source)} ↔ {graph.nodes[target].get('label', target)}<br>{attrs.get('support_count', 0)} supporting papers",
                }
            )

        top_entities_by_type = self._top_entities_by_type(filtered_nodes_df)
        top_edges = self._top_edges(edges_df, node_lookup)
        diagnostics |= {
            'final_node_count': int(len(graph_nodes)),
            'final_edge_count': int(len(graph_edges)),
            'signal': self._signal_quality(len(graph_nodes), len(graph_edges)),
        }

        return {
            'graph': {'nodes': graph_nodes, 'edges': graph_edges},
            'node_details': node_details,
            'edge_details': edge_details,
            'top_edges': top_edges,
            'top_entities_by_type': top_entities_by_type,
            'node_table': filtered_nodes_df.sort_values(['support_count', 'label'], ascending=[False, True]).to_dict(orient='records'),
            'edge_table': edges_df.sort_values(['support_count', 'source_id'], ascending=[False, True]).to_dict(orient='records'),
            'diagnostics': diagnostics,
        }

    def _aggregate_nodes(self, entities_df: pd.DataFrame) -> pd.DataFrame:
        grouped = (
            entities_df.groupby(['entity_id', 'entity_type', 'normalized_id'], dropna=False)
            .agg(
                support_count=('pmid', pd.Series.nunique),
                aliases=('entity_text', lambda values: sorted({str(v).strip() for v in values if str(v).strip()})),
            )
            .reset_index()
        )
        grouped['label'] = grouped.apply(
            lambda row: choose_display_label(row['aliases'], str(row['entity_type']), str(row['normalized_id'])),
            axis=1,
        )
        return grouped

    def _drop_generic_nodes(self, nodes_df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
        if nodes_df.empty:
            return nodes_df, 0
        keep_mask = nodes_df.apply(self._should_keep_node, axis=1)
        removed = int((~keep_mask).sum())
        return nodes_df.loc[keep_mask].copy(), removed

    def _should_keep_node(self, row: pd.Series) -> bool:
        label = str(row.get('label', '')).strip().lower()
        normalized_id = str(row.get('normalized_id', '')).strip()
        entity_type = str(row.get('entity_type', '')).strip()
        if normalized_id in self.GENERIC_NORMALIZED_IDS:
            return False
        if label in self.GENERIC_LABELS_BY_TYPE.get(entity_type, set()):
            return False
        if not label or label in {'-', '--'}:
            return False
        return True

    def _build_cooccurrence_edges(self, mentions_df: pd.DataFrame) -> pd.DataFrame:
        edge_map: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {'edge_kind': 'cooccurrence', 'relation_label': '', 'pmids': set()})
        for pmid, chunk in mentions_df.groupby('pmid'):
            unique_entities = sorted(set(chunk['entity_id']))
            for left, right in combinations(unique_entities, 2):
                key = tuple(sorted((left, right)))
                edge_map[key]['pmids'].add(str(pmid))
        rows = []
        for (source_id, target_id), payload in edge_map.items():
            rows.append(
                {
                    'source_id': source_id,
                    'target_id': target_id,
                    'edge_kind': payload['edge_kind'],
                    'relation_label': payload['relation_label'],
                    'support_count': len(payload['pmids']),
                    'pmids': sorted(payload['pmids']),
                }
            )
        return pd.DataFrame(rows)

    def _build_relation_edges(self, relations_df: pd.DataFrame, kept_nodes: set[str]) -> pd.DataFrame:
        if relations_df.empty:
            return pd.DataFrame(columns=['source_id', 'target_id', 'edge_kind', 'relation_label', 'support_count', 'pmids'])
        edge_map: dict[tuple[str, str], dict[str, Any]] = defaultdict(lambda: {'edge_kind': 'relation', 'relation_label': set(), 'pmids': set()})
        for _, row in relations_df.iterrows():
            source_id = row['source_id']
            target_id = row['target_id']
            if source_id not in kept_nodes or target_id not in kept_nodes:
                continue
            key = tuple(sorted((source_id, target_id)))
            edge_map[key]['relation_label'].add(str(row.get('relation_label', 'related_to')))
            edge_map[key]['pmids'].add(str(row['pmid']))
        rows = []
        for (source_id, target_id), payload in edge_map.items():
            rows.append(
                {
                    'source_id': source_id,
                    'target_id': target_id,
                    'edge_kind': 'relation',
                    'relation_label': '; '.join(sorted(payload['relation_label'])),
                    'support_count': len(payload['pmids']),
                    'pmids': sorted(payload['pmids']),
                }
            )
        return pd.DataFrame(rows)

    def _merge_edges(self, cooccurrence_df: pd.DataFrame, relation_df: pd.DataFrame) -> pd.DataFrame:
        if cooccurrence_df.empty:
            return relation_df
        if relation_df.empty:
            return cooccurrence_df

        merged: dict[tuple[str, str], dict[str, Any]] = {}
        for frame in [cooccurrence_df, relation_df]:
            for _, row in frame.iterrows():
                key = tuple(sorted((row['source_id'], row['target_id'])))
                if key not in merged:
                    merged[key] = {
                        'source_id': key[0],
                        'target_id': key[1],
                        'edge_kind': row['edge_kind'],
                        'relation_label': row.get('relation_label', ''),
                        'pmids': set(row.get('pmids', [])),
                    }
                else:
                    merged[key]['pmids'].update(row.get('pmids', []))
                    if row['edge_kind'] == 'relation':
                        merged[key]['edge_kind'] = 'relation'
                        labels = {label for label in [merged[key]['relation_label'], row.get('relation_label', '')] if label}
                        merged[key]['relation_label'] = '; '.join(sorted(labels))
        rows = []
        for payload in merged.values():
            rows.append(
                {
                    'source_id': payload['source_id'],
                    'target_id': payload['target_id'],
                    'edge_kind': payload['edge_kind'],
                    'relation_label': payload['relation_label'],
                    'support_count': len(payload['pmids']),
                    'pmids': sorted(payload['pmids']),
                }
            )
        return pd.DataFrame(rows)

    def _top_entities_by_type(self, nodes_df: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for entity_type, chunk in nodes_df.groupby('entity_type'):
            subset = chunk.sort_values(['support_count', 'label'], ascending=[False, True]).head(8)
            grouped[str(entity_type)] = subset.to_dict(orient='records')
        return grouped

    def _top_edges(self, edges_df: pd.DataFrame, node_lookup: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        if edges_df.empty:
            return []
        rows = []
        for _, row in edges_df.sort_values(['support_count', 'source_id'], ascending=[False, True]).head(12).iterrows():
            rows.append(
                {
                    'source_label': node_lookup.get(row['source_id'], {}).get('label', row['source_id']),
                    'target_label': node_lookup.get(row['target_id'], {}).get('label', row['target_id']),
                    'source_type': node_lookup.get(row['source_id'], {}).get('entity_type', ''),
                    'target_type': node_lookup.get(row['target_id'], {}).get('entity_type', ''),
                    'edge_kind': row['edge_kind'],
                    'relation_label': humanize_relation_label(row.get('relation_label', ''), row['edge_kind']),
                    'support_count': int(row['support_count']),
                    'pmids': row.get('pmids', []),
                }
            )
        return rows

    def _signal_quality(self, node_count: int, edge_count: int) -> str:
        if node_count >= 15 and edge_count >= 20:
            return 'strong'
        if node_count >= 5 and edge_count >= 4:
            return 'moderate'
        return 'low'

    def _paper_card(self, pmid: str, paper_lookup: dict[str, dict[str, Any]]) -> dict[str, Any]:
        paper = paper_lookup.get(str(pmid), {})
        return {
            'pmid': str(pmid),
            'title': paper.get('title', f'PMID {pmid}'),
            'journal': paper.get('journal', 'Unknown journal'),
            'pub_date': paper.get('pub_date', ''),
            'year': paper.get('year'),
        }

    def _empty_payload(self) -> dict[str, Any]:
        return {
            'graph': {'nodes': [], 'edges': []},
            'node_details': {},
            'edge_details': {},
            'top_edges': [],
            'top_entities_by_type': {},
            'node_table': [],
            'edge_table': [],
            'diagnostics': {'raw_node_count': 0, 'generic_nodes_removed': 0, 'isolated_nodes_removed': 0, 'final_node_count': 0, 'final_edge_count': 0, 'signal': 'low'},
        }
