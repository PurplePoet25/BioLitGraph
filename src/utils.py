from __future__ import annotations

import json
import re
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r'[^a-z0-9]+', '-', value)
    return value.strip('-') or 'query'


class RequestThrottler:
    def __init__(self, requests_per_second: float = 3.0):
        self.min_interval = 1.0 / max(requests_per_second, 0.1)
        self._last_request_at = 0.0

    def wait(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        remaining = self.min_interval - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_request_at = time.monotonic()


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


YEAR_PATTERN = re.compile(r'(19|20)\d{2}')


def extract_year(value: str | None) -> int | None:
    if not value:
        return None
    match = YEAR_PATTERN.search(str(value))
    if match:
        return int(match.group(0))
    return None


DATE_FORMATS = ['%Y %b %d', '%Y %b', '%Y', '%Y-%m-%d', '%Y/%m/%d']


def safe_date_range(years: Iterable[int | None]) -> str:
    valid = sorted(y for y in years if y)
    if not valid:
        return 'Unknown'
    if len(valid) == 1:
        return str(valid[0])
    return f'{valid[0]}–{valid[-1]}'


def dominant_text(values: Iterable[str]) -> str:
    cleaned = [str(v).strip() for v in values if str(v).strip()]
    if not cleaned:
        return 'Unknown'
    return Counter(cleaned).most_common(1)[0][0]


def clean_identifier(value: Any) -> str:
    text = str(value or '').strip()
    if not text or text in {'-', '--', 'None', 'null', 'NULL', 'N/A', 'n/a'}:
        return ''
    # PubTator sometimes joins multiple IDs with delimiters. Keep the first stable one for v1.
    for delimiter in (';', '|', ','):
        if delimiter in text:
            first = next((part.strip() for part in text.split(delimiter) if part.strip()), '')
            if first and first not in {'-', '--'}:
                return first
    return text


_ABBREV_PATTERN = re.compile(r'^[A-Z0-9][A-Z0-9\-]{1,6}$')


def choose_display_label(values: Iterable[str], entity_type: str, normalized_id: str = '') -> str:
    aliases = [str(v).strip() for v in values if str(v).strip()]
    if not aliases:
        return normalized_id or 'Unknown'

    counts = Counter(aliases)
    label = counts.most_common(1)[0][0]

    # Prefer fuller labels for chemicals if the dominant label is an opaque abbreviation.
    if entity_type == 'Chemical' and _ABBREV_PATTERN.fullmatch(label or ''):
        candidates = [a for a in aliases if len(a) > len(label) + 3 and not _ABBREV_PATTERN.fullmatch(a)]
        if candidates:
            return sorted(candidates, key=lambda item: (-counts[item], len(item), item.lower()))[0]

    # For genes, keep familiar symbols like EGFR/TP53, but upgrade vague roots like BRCA -> BRCA1 when possible.
    if entity_type == 'Gene' and _ABBREV_PATTERN.fullmatch(label or ''):
        candidates = [
            a for a in aliases
            if a != label and (any(ch.isdigit() for ch in a) or '-' in a) and a.upper().startswith(label.upper())
        ]
        if candidates:
            return sorted(candidates, key=lambda item: (-counts[item], len(item), item.lower()))[0]

    # For diseases, prefer a fuller alias when the dominant label is a short acronym but a clear long form exists.
    if entity_type == 'Disease' and _ABBREV_PATTERN.fullmatch(label or '') and len(label) <= 5:
        candidates = [a for a in aliases if len(a) > len(label) + 6 and ' ' in a]
        if candidates:
            return sorted(candidates, key=lambda item: (-counts[item], len(item), item.lower()))[0]

    return label


def humanize_relation_label(label: str | None, edge_kind: str = '') -> str:
    text = str(label or '').strip()
    if not text:
        return 'Co-occurrence' if edge_kind == 'cooccurrence' else 'Related'
    pieces: list[str] = []
    for raw_piece in text.split(';'):
        piece = raw_piece.strip().replace('_', ' ')
        if not piece:
            continue
        piece = re.sub(r'\s+', ' ', piece)
        pieces.append(piece[:1].upper() + piece[1:])
    return '; '.join(dict.fromkeys(pieces)) or ('Co-occurrence' if edge_kind == 'cooccurrence' else 'Related')


def write_json(path: Path, payload: Any) -> None:
    ensure_directory(path.parent)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')


def timestamp_slug() -> str:
    return datetime.now().strftime('%Y%m%d-%H%M%S')
