from __future__ import annotations

from typing import Any

import pandas as pd

from src.analytics import build_summary, build_timeline
from src.clients.pubmed_client import PubMedClient
from src.clients.pubtator_client import PubTatorClient
from src.config import settings
from src.demo import DemoLoader
from src.graph_builder import GraphBuilder
from src.parsers import parse_pubtator_biocjson, parse_pubtator_pubtator
from src.utils import ensure_directory, slugify, timestamp_slug, write_json


class BioLitGraphPipeline:
    def __init__(self) -> None:
        self.pubmed = PubMedClient()
        self.pubtator = PubTatorClient()
        self.demo_loader = DemoLoader()
        self.graph_builder = GraphBuilder(min_node_support=2, min_edge_support=2)

    def run(self, query: str, retmax: int = 60, source: str = 'live') -> dict[str, Any]:
        run_id = f"{timestamp_slug()}-{slugify(query)[:45]}"
        run_dir = settings.runs_dir / run_id
        ensure_directory(run_dir)
        parser_mode = 'demo'

        if source == 'demo':
            papers_df, entities_df, relations_df = self.demo_loader.load()
            papers_df['query_used'] = query
        else:
            search_result = self.pubmed.search(query, retmax=retmax)
            ids = search_result['ids']
            if not ids:
                raise RuntimeError('PubMed returned no papers for that query. Try a broader topic or switch to demo mode.')
            papers = self.pubmed.fetch_summaries(ids, webenv=search_result['webenv'], query_key=search_result['query_key'])
            papers_df = pd.DataFrame(papers)
            if papers_df.empty:
                raise RuntimeError('PubMed search worked, but no paper summaries were returned.')
            papers_df['query_used'] = query

            documents = self.pubtator.fetch_annotations(ids)
            if not documents:
                raise RuntimeError(
                    'PubTator did not return annotation data. Check your internet connection or try the bundled demo mode.'
                )
            write_json(run_dir / 'pubtator_raw.json', {'payload': documents})
            entities_df, relations_df = parse_pubtator_biocjson(documents)
            parser_mode = 'biocjson'

            if entities_df.empty:
                raw_text = self.pubtator.fetch_annotations_text(ids)
                if raw_text.strip():
                    (run_dir / 'pubtator_raw.txt').write_text(raw_text, encoding='utf-8')
                    text_entities_df, text_relations_df = parse_pubtator_pubtator(raw_text)
                    if not text_entities_df.empty:
                        entities_df, relations_df = text_entities_df, text_relations_df
                        parser_mode = 'pubtator-text-fallback'

            if entities_df.empty:
                raise RuntimeError(
                    'PubTator returned data, but BioLitGraph could not parse supported entities from the live response. '
                    'I saved the raw PubTator response inside this run folder so we can inspect it.'
                )

        graph_payload = self.graph_builder.build(papers_df, entities_df, relations_df)
        timeline = build_timeline(papers_df)
        summary = build_summary(query=query, source=source, papers_df=papers_df, entities_df=entities_df, graph_payload=graph_payload)
        summary['parser_mode'] = parser_mode
        summary['signal'] = graph_payload.get('diagnostics', {}).get('signal', 'low')

        papers_path = run_dir / 'papers.csv'
        entities_path = run_dir / 'entities.csv'
        relations_path = run_dir / 'relations.csv'
        graph_path = run_dir / 'graph.json'
        papers_df.to_csv(papers_path, index=False)
        entities_df.to_csv(entities_path, index=False)
        relations_df.to_csv(relations_path, index=False)
        write_json(graph_path, graph_payload)

        bundle = {
            'run_id': run_id,
            'summary': summary,
            'timeline': timeline,
            'papers': papers_df.sort_values(['year', 'title'], ascending=[False, True]).to_dict(orient='records'),
            'top_entities_by_type': graph_payload['top_entities_by_type'],
            'top_edges': graph_payload['top_edges'],
            'graph': graph_payload['graph'],
            'node_details': graph_payload['node_details'],
            'edge_details': graph_payload['edge_details'],
            'diagnostics': graph_payload.get('diagnostics', {}),
            'outputs': {
                'papers_csv': str(papers_path.relative_to(settings.base_dir)).replace('\\', '/'),
                'entities_csv': str(entities_path.relative_to(settings.base_dir)).replace('\\', '/'),
                'relations_csv': str(relations_path.relative_to(settings.base_dir)).replace('\\', '/'),
                'graph_json': str(graph_path.relative_to(settings.base_dir)).replace('\\', '/'),
            },
        }
        write_json(run_dir / 'bundle.json', bundle)
        return bundle
