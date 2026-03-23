from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd

from src.utils import clean_identifier

ENTITY_TYPE_MAP = {
    'gene': 'Gene',
    'gene/protein': 'Gene',
    'genes/proteins': 'Gene',
    'protein': 'Gene',
    'disease': 'Disease',
    'chemical': 'Chemical',
    'drug': 'Chemical',
    'variant': 'Variant',
    'mutation': 'Variant',
    'cellline': 'CellLine',
    'cell line': 'CellLine',
    'cell_line': 'CellLine',
}

ALLOWED_ENTITY_TYPES = {'Gene', 'Disease', 'Chemical', 'Variant', 'CellLine'}


def normalize_entity_type(raw_type: str | None) -> str | None:
    if not raw_type:
        return None
    cleaned = str(raw_type).strip().lower()
    normalized = ENTITY_TYPE_MAP.get(cleaned)
    if normalized:
        return normalized
    return raw_type if raw_type in ALLOWED_ENTITY_TYPES else None


def extract_identifier(infons: dict[str, Any]) -> str:
    candidate_keys = [
        'identifier',
        'Identifier',
        'normalized',
        'normalized_id',
        'id',
        'IdentifierList',
        'identifier_list',
    ]
    for key in candidate_keys:
        value = clean_identifier(infons.get(key))
        if value:
            return value
    for key, value in infons.items():
        if key.lower().endswith('identifier'):
            candidate = clean_identifier(value)
            if candidate:
                return candidate
    return ''


def _normalize_documents(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    for key in ('documents', 'docs', 'collection', 'items', 'results'):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    if any(key in payload for key in ('id', 'pmid', 'passages', 'annotations', 'denotations', 'relations')):
        return [payload]

    if all(isinstance(value, dict) for value in payload.values()):
        values = [value for value in payload.values() if isinstance(value, dict)]
        if values:
            return values

    return []


def _first_location(annotation: dict[str, Any]) -> dict[str, Any]:
    locations = annotation.get('locations') or annotation.get('location') or annotation.get('span') or []
    if isinstance(locations, dict):
        locations = [locations]
    if not locations:
        return {}
    return locations[0] or {}


def _offset_and_length(location: dict[str, Any]) -> tuple[int, int]:
    offset = location.get('offset', location.get('begin', 0)) or 0
    if 'length' in location and location.get('length') is not None:
        length = location.get('length', 0) or 0
    else:
        end = location.get('end')
        length = (end - offset) if end is not None else 0
    return int(offset), max(int(length), 0)


def _annotation_text(annotation: dict[str, Any]) -> str:
    return str(annotation.get('text') or annotation.get('mention') or annotation.get('obj') or annotation.get('name') or '')


def parse_pubtator_biocjson(payload: Any) -> tuple[pd.DataFrame, pd.DataFrame]:
    entity_rows: list[dict[str, Any]] = []
    relation_rows: list[dict[str, Any]] = []
    documents = _normalize_documents(payload)

    for document in documents:
        pmid = str(document.get('id') or document.get('pmid') or document.get('pmcid') or '')
        passages = document.get('passages') or []
        if not passages and (document.get('annotations') or document.get('denotations')):
            passages = [
                {
                    'infons': {'type': 'document'},
                    'annotations': document.get('annotations') or document.get('denotations') or [],
                }
            ]

        doc_relations = document.get('relations') or document.get('relationships') or []
        annotation_lookup: dict[str, str] = {}

        for passage in passages:
            section = str((passage.get('infons') or {}).get('type', 'unknown'))
            annotations = passage.get('annotations') or passage.get('denotations') or []
            for annotation in annotations:
                infons = annotation.get('infons', {}) or {}
                entity_type = normalize_entity_type(
                    infons.get('type') or infons.get('concept') or infons.get('category') or annotation.get('obj') or annotation.get('type')
                )
                if entity_type not in ALLOWED_ENTITY_TYPES:
                    continue
                text = _annotation_text(annotation).strip()
                normalized_id = extract_identifier(infons) or text
                location = _first_location(annotation)
                offset, length = _offset_and_length(location)
                mention_id = str(annotation.get('id') or annotation.get('@id') or f'{pmid}:{offset}:{text}')
                entity_id = f'{entity_type}:{normalized_id}'
                annotation_lookup[mention_id] = entity_id
                if normalized_id:
                    annotation_lookup[normalized_id] = entity_id
                if text:
                    annotation_lookup[text] = entity_id
                entity_rows.append(
                    {
                        'pmid': pmid,
                        'entity_id': entity_id,
                        'entity_text': text,
                        'entity_type': entity_type,
                        'normalized_id': normalized_id,
                        'source_passage': section,
                        'char_offset': offset,
                        'length': length,
                    }
                )

        for relation in doc_relations:
            infons = relation.get('infons', {}) or {}
            relation_type = str(infons.get('type') or infons.get('relation') or relation.get('type') or 'related_to')
            nodes = relation.get('nodes') or []
            resolved_nodes: list[str] = []

            if isinstance(nodes, list) and len(nodes) >= 2:
                for node in nodes[:2]:
                    refid = str(node.get('refid') or node.get('id') or node.get('identifier') or '')
                    resolved_nodes.append(annotation_lookup.get(refid, refid))
            else:
                for key in ('subj', 'subject', 'source_id', 'obj', 'object', 'target_id'):
                    if key in relation:
                        refid = str(relation.get(key) or '')
                        if refid:
                            resolved_nodes.append(annotation_lookup.get(refid, refid))
                resolved_nodes = resolved_nodes[:2]

            if len(resolved_nodes) == 2 and all(resolved_nodes):
                source_id, target_id = resolved_nodes
                relation_rows.append(
                    {
                        'pmid': pmid,
                        'source_id': source_id,
                        'target_id': target_id,
                        'relation_label': relation_type,
                        'edge_kind': 'relation',
                    }
                )

    entities_df = pd.DataFrame(entity_rows)
    relations_df = pd.DataFrame(relation_rows)
    if not entities_df.empty:
        entities_df = entities_df.drop_duplicates()
    if not relations_df.empty:
        relations_df = relations_df.drop_duplicates()
    return entities_df, relations_df


def parse_pubtator_pubtator(text: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    entity_rows: list[dict[str, Any]] = []
    relation_rows: list[dict[str, Any]] = []
    entity_lookup: dict[str, dict[str, str]] = defaultdict(dict)

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if '|t|' in line or '|a|' in line:
            continue

        parts = raw_line.split('\t')
        if len(parts) >= 6:
            pmid, start, end, mention, raw_type, identifier = parts[:6]
            entity_type = normalize_entity_type(raw_type)
            if entity_type not in ALLOWED_ENTITY_TYPES:
                continue
            normalized_id = clean_identifier(identifier) or str(mention or '').strip()
            entity_id = f'{entity_type}:{normalized_id}'
            start_i = int(start) if str(start).isdigit() else 0
            end_i = int(end) if str(end).isdigit() else start_i
            entity_rows.append(
                {
                    'pmid': str(pmid),
                    'entity_id': entity_id,
                    'entity_text': str(mention).strip(),
                    'entity_type': entity_type,
                    'normalized_id': normalized_id,
                    'source_passage': 'document',
                    'char_offset': start_i,
                    'length': max(end_i - start_i, 0),
                }
            )
            entity_lookup[str(pmid)][normalized_id] = entity_id
            entity_lookup[str(pmid)][str(mention).strip()] = entity_id
        elif len(parts) >= 4:
            pmid, relation_label, source_ref, target_ref = parts[:4]
            lookup = entity_lookup.get(str(pmid), {})
            source_id = lookup.get(str(source_ref), str(source_ref))
            target_id = lookup.get(str(target_ref), str(target_ref))
            if source_id and target_id:
                relation_rows.append(
                    {
                        'pmid': str(pmid),
                        'source_id': source_id,
                        'target_id': target_id,
                        'relation_label': str(relation_label or 'related_to'),
                        'edge_kind': 'relation',
                    }
                )

    entities_df = pd.DataFrame(entity_rows)
    relations_df = pd.DataFrame(relation_rows)
    if not entities_df.empty:
        entities_df = entities_df.drop_duplicates()
    if not relations_df.empty:
        relations_df = relations_df.drop_duplicates()
    return entities_df, relations_df
