from __future__ import annotations

from src.parsers import parse_pubtator_biocjson, parse_pubtator_pubtator


BIOC_SAMPLE = [
    {
        'id': '12345',
        'passages': [
            {
                'infons': {'type': 'abstract'},
                'annotations': [
                    {
                        'id': 'T1',
                        'infons': {'type': 'Gene', 'identifier': 'EGFR'},
                        'text': 'EGFR',
                        'locations': [{'offset': 0, 'length': 4}],
                    },
                    {
                        'id': 'T2',
                        'infons': {'type': 'Disease', 'identifier': 'D:NSCLC'},
                        'text': 'non-small cell lung cancer',
                        'locations': [{'offset': 15, 'length': 27}],
                    },
                ],
            }
        ],
        'relations': [
            {
                'infons': {'type': 'associate'},
                'nodes': [{'refid': 'T1'}, {'refid': 'T2'}],
            }
        ],
    }
]


PUBTATOR_TEXT_SAMPLE = """12345|t|EGFR and lung cancer
12345|a|EGFR is implicated in non-small cell lung cancer.
12345\t0\t4\tEGFR\tGene\tEGFR
12345\t28\t55\tnon-small cell lung cancer\tDisease\tD:NSCLC
12345\tassociate\tEGFR\tD:NSCLC
"""


def test_parse_pubtator_biocjson_extracts_entities_and_relations():
    entities_df, relations_df = parse_pubtator_biocjson(BIOC_SAMPLE)
    assert len(entities_df) == 2
    assert entities_df['entity_type'].tolist() == ['Gene', 'Disease']
    assert len(relations_df) == 1
    assert relations_df.iloc[0]['relation_label'] == 'associate'


def test_parse_pubtator_biocjson_accepts_wrapper_payloads():
    payload = {'documents': BIOC_SAMPLE}
    entities_df, relations_df = parse_pubtator_biocjson(payload)
    assert len(entities_df) == 2
    assert len(relations_df) == 1


def test_parse_pubtator_text_extracts_entities_and_relations():
    entities_df, relations_df = parse_pubtator_pubtator(PUBTATOR_TEXT_SAMPLE)
    assert len(entities_df) == 2
    assert set(entities_df['entity_type']) == {'Gene', 'Disease'}
    assert len(relations_df) == 1
    assert relations_df.iloc[0]['source_id'] == 'Gene:EGFR'


def test_parse_pubtator_treats_dash_identifier_as_missing():
    payload = {
        'documents': [
            {
                'id': '9',
                'passages': [
                    {
                        'infons': {'type': 'abstract'},
                        'annotations': [
                            {'id': 'T1', 'infons': {'type': 'Chemical', 'identifier': '-'}, 'text': 'essential oils'},
                            {'id': 'T2', 'infons': {'type': 'Chemical', 'identifier': '-'}, 'text': 'lysozyme'},
                        ],
                    }
                ],
            }
        ]
    }
    entities_df, _ = parse_pubtator_biocjson(payload)
    assert set(entities_df['normalized_id']) == {'essential oils', 'lysozyme'}
    assert len(set(entities_df['entity_id'])) == 2
