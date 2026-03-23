from __future__ import annotations

from typing import Any

import requests

from src.config import settings
from src.utils import RequestThrottler, extract_year


class PubMedClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.throttler = RequestThrottler(settings.ncbi_requests_per_second)

    def _request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        self.throttler.wait()
        payload = {
            'tool': settings.ncbi_tool,
            'email': settings.ncbi_email,
            **params,
        }
        if settings.ncbi_api_key:
            payload['api_key'] = settings.ncbi_api_key
        response = self.session.get(
            f'{settings.ncbi_base_url}/{endpoint}',
            params=payload,
            timeout=settings.request_timeout,
        )
        response.raise_for_status()
        return response.json()

    def search(self, query: str, retmax: int = 60) -> dict[str, Any]:
        data = self._request(
            'esearch.fcgi',
            {
                'db': 'pubmed',
                'term': query,
                'retmax': retmax,
                'retmode': 'json',
                'sort': 'relevance',
                'usehistory': 'y',
            },
        )
        result = data.get('esearchresult', {})
        ids = result.get('idlist', [])
        return {
            'count': int(result.get('count', 0) or 0),
            'ids': ids,
            'webenv': result.get('webenv', ''),
            'query_key': result.get('querykey', ''),
            'query_translation': result.get('querytranslation', ''),
        }

    def fetch_summaries(
        self,
        ids: list[str],
        webenv: str = '',
        query_key: str = '',
        batch_size: int = 200,
    ) -> list[dict[str, Any]]:
        if not ids:
            return []

        records: list[dict[str, Any]] = []
        for start in range(0, len(ids), batch_size):
            chunk = ids[start:start + batch_size]
            params: dict[str, Any] = {'db': 'pubmed', 'retmode': 'json'}
            if webenv and query_key:
                params.update(
                    {
                        'query_key': query_key,
                        'WebEnv': webenv,
                        'retstart': start,
                        'retmax': len(chunk),
                    }
                )
            else:
                params['id'] = ','.join(chunk)

            data = self._request('esummary.fcgi', params)
            result = data.get('result', {})
            uids = result.get('uids', [])
            for uid in uids:
                item = result.get(uid, {})
                pub_date = item.get('pubdate') or item.get('epubdate') or ''
                records.append(
                    {
                        'pmid': str(uid),
                        'title': (item.get('title') or '').rstrip('.'),
                        'journal': item.get('fulljournalname') or item.get('source') or 'Unknown',
                        'pub_date': pub_date,
                        'year': extract_year(pub_date),
                    }
                )
        return records
