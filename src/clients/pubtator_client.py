from __future__ import annotations

from typing import Any

import requests

from src.config import settings
from src.utils import RequestThrottler


class PubTatorClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.throttler = RequestThrottler(2.8)

    def _get(self, endpoint: str, params: dict[str, Any], timeout: int | None = None) -> requests.Response:
        """Make a tolerant GET request.

        PubTator's export endpoints appear to be sensitive to explicit Accept headers on some
        representations, so we let requests send its default Accept: */* and only fall back to
        an explicit header if needed.
        """
        self.throttler.wait()
        response = self.session.get(
            f'{settings.pubtator_base_url}{endpoint}',
            params=params,
            timeout=timeout or settings.request_timeout,
        )
        # If the server refuses content negotiation, retry without any session-level oddities.
        if response.status_code == 406:
            fresh = requests.get(
                f'{settings.pubtator_base_url}{endpoint}',
                params=params,
                timeout=timeout or settings.request_timeout,
            )
            return fresh
        return response

    def fetch_annotations(self, pmids: list[str], fmt: str = 'biocjson') -> Any:
        if not pmids:
            return []

        documents: list[dict[str, Any]] = []
        wrapper_payloads: list[dict[str, Any]] = []
        # Keep chunks modest; smaller batches are more tolerant of PubTator hiccups.
        for start in range(0, len(pmids), 25):
            chunk = pmids[start:start + 25]
            response = self._get(
                f'/publications/export/{fmt}',
                params={'pmids': ','.join(chunk)},
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and 'documents' in data:
                documents.extend(data['documents'])
            elif isinstance(data, list):
                documents.extend(data)
            elif isinstance(data, dict):
                wrapper_payloads.append(data)
        if documents:
            return documents
        if len(wrapper_payloads) == 1:
            return wrapper_payloads[0]
        if wrapper_payloads:
            return {'documents': wrapper_payloads}
        return []

    def fetch_annotations_text(self, pmids: list[str]) -> str:
        if not pmids:
            return ''

        chunks: list[str] = []
        # Be extra conservative for the plain-text fallback.
        for start in range(0, len(pmids), 10):
            chunk = pmids[start:start + 10]
            response = self._get(
                '/publications/export/pubtator',
                params={'pmids': ','.join(chunk)},
            )
            if response.status_code == 406 and len(chunk) > 1:
                # Fall back to one PMID at a time instead of killing the whole run.
                for pmid in chunk:
                    single = self._get('/publications/export/pubtator', params={'pmids': pmid})
                    if single.ok and single.text.strip():
                        chunks.append(single.text)
                continue
            response.raise_for_status()
            if response.text.strip():
                chunks.append(response.text)
        return '\n\n'.join(part.strip() for part in chunks if part.strip())
