from __future__ import annotations

import pandas as pd

from src.graph_builder import GraphBuilder


def test_graph_builder_keeps_supported_nodes_and_edges():
    papers = pd.DataFrame(
        [
            {'pmid': '1', 'title': 'Paper 1', 'journal': 'J1', 'pub_date': '2022', 'year': 2022},
            {'pmid': '2', 'title': 'Paper 2', 'journal': 'J2', 'pub_date': '2023', 'year': 2023},
        ]
    )
    entities = pd.DataFrame(
        [
            {'pmid': '1', 'entity_id': 'Gene:EGFR', 'entity_text': 'EGFR', 'entity_type': 'Gene', 'normalized_id': 'EGFR'},
            {'pmid': '1', 'entity_id': 'Disease:NSCLC', 'entity_text': 'non-small cell lung cancer', 'entity_type': 'Disease', 'normalized_id': 'NSCLC'},
            {'pmid': '2', 'entity_id': 'Gene:EGFR', 'entity_text': 'EGFR', 'entity_type': 'Gene', 'normalized_id': 'EGFR'},
            {'pmid': '2', 'entity_id': 'Disease:NSCLC', 'entity_text': 'NSCLC', 'entity_type': 'Disease', 'normalized_id': 'NSCLC'},
        ]
    )
    relations = pd.DataFrame(
        [
            {'pmid': '1', 'source_id': 'Gene:EGFR', 'target_id': 'Disease:NSCLC', 'relation_label': 'associate', 'edge_kind': 'relation'}
        ]
    )
    builder = GraphBuilder(min_node_support=2, min_edge_support=2)
    payload = builder.build(papers, entities, relations)
    assert len(payload['graph']['nodes']) == 2
    assert len(payload['graph']['edges']) == 1
    assert payload['top_edges'][0]['support_count'] == 2


def test_graph_builder_drops_generic_nodes_and_isolates():
    papers = pd.DataFrame(
        [
            {'pmid': '1', 'title': 'Paper 1', 'journal': 'J1', 'pub_date': '2022', 'year': 2022},
            {'pmid': '2', 'title': 'Paper 2', 'journal': 'J2', 'pub_date': '2023', 'year': 2023},
        ]
    )
    entities = pd.DataFrame(
        [
            {'pmid': '1', 'entity_id': 'Gene:TP53', 'entity_text': 'TP53', 'entity_type': 'Gene', 'normalized_id': '7157'},
            {'pmid': '1', 'entity_id': 'Disease:AML', 'entity_text': 'acute myeloid leukemia', 'entity_type': 'Disease', 'normalized_id': 'MESH:D015470'},
            {'pmid': '1', 'entity_id': 'Disease:CANCER', 'entity_text': 'cancer', 'entity_type': 'Disease', 'normalized_id': 'MESH:D009369'},
            {'pmid': '2', 'entity_id': 'Gene:TP53', 'entity_text': 'TP53', 'entity_type': 'Gene', 'normalized_id': '7157'},
            {'pmid': '2', 'entity_id': 'Disease:AML', 'entity_text': 'AML', 'entity_type': 'Disease', 'normalized_id': 'MESH:D015470'},
            {'pmid': '2', 'entity_id': 'Disease:CANCER', 'entity_text': 'tumor', 'entity_type': 'Disease', 'normalized_id': 'MESH:D009369'},
        ]
    )
    builder = GraphBuilder(min_node_support=2, min_edge_support=2)
    payload = builder.build(papers, entities, pd.DataFrame())
    labels = {node['label'] for node in payload['graph']['nodes']}
    assert 'cancer' not in labels
    assert 'tumor' not in labels
    assert labels == {'TP53', 'acute myeloid leukemia'}
    assert payload['diagnostics']['generic_nodes_removed'] >= 1
