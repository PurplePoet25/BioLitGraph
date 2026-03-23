
from __future__ import annotations

from flask import Flask, render_template, request

from src.config import settings
from src.pipeline import BioLitGraphPipeline


def create_app() -> Flask:
    app = Flask(__name__)
    pipeline = BioLitGraphPipeline()

    @app.route('/', methods=['GET'])
    def home():
        presets = [
            'EGFR AND non-small cell lung cancer',
            'APOE AND Alzheimer disease',
            'TP53 AND acute myeloid leukemia',
            'BRCA1 AND breast cancer',
        ]
        return render_template('index.html', presets=presets, settings=settings)

    @app.route('/analyze', methods=['POST'])
    def analyze():
        query = request.form.get('query', '').strip()
        source = request.form.get('source', 'live').strip().lower()
        retmax_raw = request.form.get('retmax', '60').strip()
        presets = [
            'EGFR AND non-small cell lung cancer',
            'APOE AND Alzheimer disease',
            'TP53 AND acute myeloid leukemia',
            'BRCA1 AND breast cancer',
        ]

        try:
            retmax = max(5, min(100, int(retmax_raw)))
        except ValueError:
            retmax = 60

        if not query and source != 'demo':
            return render_template(
                'index.html',
                presets=presets,
                settings=settings,
                error='Enter a PubMed query, or switch to demo mode to explore the bundled sample dataset.',
                submitted_query=query,
                submitted_source=source,
                submitted_retmax=retmax,
            )

        try:
            bundle = pipeline.run(query=query or 'EGFR AND non-small cell lung cancer', retmax=retmax, source=source)
            return render_template(
                'index.html',
                presets=presets,
                settings=settings,
                bundle=bundle,
                submitted_query=query,
                submitted_source=source,
                submitted_retmax=retmax,
            )
        except Exception as exc:  # pragma: no cover - UI safety net
            return render_template(
                'index.html',
                presets=presets,
                settings=settings,
                error=str(exc),
                submitted_query=query,
                submitted_source=source,
                submitted_retmax=retmax,
            )

    return app


app = create_app()


if __name__ == '__main__':
    app.run(debug=False)
