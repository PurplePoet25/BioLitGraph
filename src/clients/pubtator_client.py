from __future__ import annotations

from typing import Any

import requests

from src.config import settings
from src.utils import RequestThrottler


class PubTatorClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.throttler = RequestThrottler(2.8)
        self.verify = str(settings.ca_bundle_path) if settings.ca_bundle_path.is_file() else True
        self.session.verify = self.verify

    def _get(self, endpoint: str, params: dict[str, Any], timeout: int | None = None) -> requests.Response:
        self.throttler.wait()
        response = self.session.get(
            f'{settings.pubtator_base_url}{endpoint}',
            params=params,
            timeout=timeout or settings.request_timeout,
        )
        if response.status_code == 406:
            fresh = requests.get(
                f'{settings.pubtator_base_url}{endpoint}',
                params=params,
                timeout=timeout or settings.request_timeout,
                verify=self.verify,
            )
            return fresh
        return response

    def fetch_annotations(self, pmids: list[str], fmt: str = 'biocjson') -> Any:
        if not pmids:
            return []

        documents: list[dict[str, Any]] = []
        wrapper_payloads: list[dict[str, Any]] = []
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
        for start in range(0, len(pmids), 10):
            chunk = pmids[start:start + 10]
            response = self._get(
                '/publications/export/pubtator',
                params={'pmids': ','.join(chunk)},
            )
            if response.status_code == 406 and len(chunk) > 1:
                for pmid in chunk:
                    single = self._get('/publications/export/pubtator', params={'pmids': pmid})
                    if single.ok and single.text.strip():
                        chunks.append(single.text)
                continue
            response.raise_for_status()
            if response.text.strip():
                chunks.append(response.text)
        return '\n\n'.join(part.strip() for part in chunks if part.strip())
