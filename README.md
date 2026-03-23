# BioLitGraph

BioLitGraph is a local biomedical literature intelligence tool. You give it a topic like **EGFR AND non-small cell lung cancer**, and it pulls relevant PubMed papers, asks PubTator to mark the biological entities inside those papers, then turns the whole thing into an interactive knowledge graph you can explore in your browser.

This project is meant to feel like more than “a dashboard with a biology sticker.” The real story is this:

> **BioLitGraph converts messy biomedical literature into structured, explorable biological knowledge.**

That means the project shows API work, biomedical NLP, entity normalization, graph analytics, data cleaning, and front-end thinking in one repo.

---

## What the app does

For a single topic query, BioLitGraph can:

- search PubMed for the top relevant papers
- collect paper metadata such as PMID, title, journal, and publication date
- fetch PubTator annotations for those PMIDs
- extract **genes, diseases, chemicals, variants, and cell lines**
- collapse repeated mentions into normalized entities
- build a graph where nodes are entities and edges are connections supported by papers
- show top entities, top edges, a timeline, a paper table, and a click-to-inspect graph
- save the run as CSV + JSON outputs

There is also a **bundled demo mode** so the full UI can be tested immediately even if the live APIs are unavailable.

---

## How it works in plain English

This is the easiest version to explain in a README, interview, or presentation.

### 1) Retrieval layer

You type a biomedical topic.

BioLitGraph sends that topic to **PubMed** using NCBI’s E-utilities API. PubMed returns the PMIDs for the most relevant papers, and then the app fetches summary metadata for those papers.

At this point, the app knows things like:

- which papers matched the query
- what their titles are
- which journals they came from
- when they were published

### 2) Annotation layer

Next, BioLitGraph sends those PMIDs to **PubTator 3**.

PubTator is an AI-powered biomedical annotation system. It reads the literature and tags important biological concepts such as genes, diseases, chemicals, variants, species, and cell lines.

For this project, v1 focuses on the entity types that are most useful for a compact literature graph:

- Gene
- Disease
- Chemical
- Variant
- CellLine

PubTator also tries to normalize mentions into standard identifiers. That matters because papers do not all use the same wording. One paper might say **EGFR**, another might say **epidermal growth factor receptor**, and a third might use a variant description. The app tries to collapse those repeated mentions into one normalized entity node instead of treating them like totally separate things.

### 3) Graph layer

Once the entities are parsed, the backend turns them into a graph.

- **Nodes** = normalized biological entities
- **Edges** = connections between entities
- **Edge weight** = number of distinct papers supporting that connection

There are two ways an edge can exist:

1. **Relation edge**: PubTator explicitly extracted a relation.
2. **Co-occurrence edge**: two entities appear in the same paper, so the app connects them as a weaker signal.

The graph builder also filters noise. A giant literature graph can become unreadable very quickly, so v1 keeps only entities and edges that appear in at least **two** papers by default.

### 4) App layer

The Flask app sends the final graph data to the browser.

The front end then renders:

- an interactive graph
- top entities by type
- top edges by support
- a publication timeline
- a details panel that updates when you click a node or edge
- a paper table with PubMed links

The details panel is important because it turns the graph from “pretty network picture” into “something you can actually interpret.”

---

## What is happening behind the scenes

If you want a slightly more technical explanation without becoming unreadable, this is the sweet spot.

### PubMed client

The PubMed client does two main jobs:

1. `esearch` — find PMIDs for a query
2. `esummary` — fetch metadata for those PMIDs

The client includes:

- polite request throttling
- `tool` and `email` parameters for NCBI requests
- optional support for an NCBI API key through `.env`
- JSON parsing into tidy paper records

### PubTator client

The PubTator client requests annotations in **BioC JSON** format. It chunks PMIDs in batches so one run does not try to fetch everything in a single request.

### Parser

The parser walks through PubTator documents and pulls out:

- PMID
- entity text
- entity type
- normalized identifier
- source passage / section
- extracted relations, when they exist

### Graph builder

The graph builder aggregates all repeated mentions of the same entity and creates:

- a node table
- an edge table
- `node_details` for the front-end details panel
- `edge_details` for the front-end details panel
- graph-ready node/edge JSON

### Analytics

The analytics layer adds:

- summary metrics
- publication timeline counts by year
- top entities by type
- strongest edges by support count

### Output files

Each run writes files to `outputs/runs/<run_id>/`, including lightweight diagnostics so you can see how many generic or isolated nodes were filtered before the final graph was rendered.

That makes the app reproducible and inspectable. You can always go back and inspect:

- `papers.csv`
- `entities.csv`
- `relations.csv`
- `graph.json`
- `bundle.json`

---

## Why the repo is structured this way

This repo is split by responsibility so the project stays readable.

```text
BioLitGraph/
├─ app.py                    # Flask entry point
├─ src/
│  ├─ config.py              # environment variables and paths
│  ├─ utils.py               # helper utilities like throttling and slugifying
│  ├─ analytics.py           # summary metrics and timeline prep
│  ├─ demo.py                # bundled demo dataset loader
│  ├─ parsers.py             # PubTator BioC JSON parsing
│  ├─ graph_builder.py       # entity aggregation + graph construction
│  ├─ pipeline.py            # end-to-end orchestration
│  └─ clients/
│     ├─ pubmed_client.py    # PubMed E-utilities calls
│     └─ pubtator_client.py  # PubTator 3 export calls
├─ templates/
│  ├─ base.html
│  └─ index.html
├─ static/
│  ├─ css/styles.css
│  └─ js/app.js
├─ data/
│  ├─ demo/                  # bundled sample dataset for offline testing
│  ├─ raw/
│  ├─ interim/
│  └─ processed/
├─ outputs/
│  └─ runs/
├─ tests/
│  ├─ test_graph_builder.py
│  └─ test_parsers.py
├─ requirements.txt
└─ README.md
```

This layout makes it obvious where each part of the project lives.

---

## Why Flask instead of Streamlit

Streamlit is great for quick data apps, but this project uses **Flask + Jinja templates + custom JavaScript** because that gives much more control over the visual design and the interaction model.

That matters here because the graph needs a dedicated details panel, custom click behavior, and a cleaner app-like layout.

So the architecture is:

- **Flask** for routing and server-side rendering
- **HTML/CSS** for layout and style
- **vanilla JavaScript** for graph interactions and details panel updates
- **vis-network** in the browser for the network view
- **Plotly.js** in the browser for the timeline

---

## How to run it

### 1) Clone the repo and create a virtual environment

```bash
git clone <your-repo-url>
cd BioLitGraph
python -m venv .venv
```

### 2) Activate the environment

#### macOS / Linux

```bash
source .venv/bin/activate
```

#### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

#### Windows Command Prompt

```cmd
.venv\Scripts\activate.bat
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Optional: create a `.env` file

```env
NCBI_EMAIL=your_email@example.com
NCBI_TOOL=BioLitGraph
NCBI_API_KEY=your_ncbi_api_key_here
REQUEST_TIMEOUT=30
```

You can still run the app without an API key. The key mainly gives higher request limits.

### 5) Start the app

```bash
flask --app app run
```

Then open:

```text
http://127.0.0.1:5000
```

---

## First thing to test

Use **demo mode** first.

Why? Because it proves that the front end, graph building, details panel, timeline, and table rendering all work before you touch the live APIs.

Then switch to **live mode** and try one of these:

- `EGFR AND non-small cell lung cancer`
- `APOE AND Alzheimer disease`
- `TP53 AND acute myeloid leukemia`
- `BRCA1 AND breast cancer`

---

## What a good v1 run should produce

A successful run should give you:

- a graph with a readable number of nodes and edges
- a timeline with year counts
- top entities grouped by type
- top edges ranked by supporting papers
- a paper table with PubMed links
- saved CSV and JSON outputs in the run folder

If the graph looks too dense, reduce noise by:

- lowering the paper limit
- using a more specific query
- raising the minimum node or edge support threshold in `GraphBuilder`

---

## Limitations of v1

This version is intentionally focused.

- It does **not** use full-text PMC parsing yet.
- It does **not** compare multiple queries side by side yet.
- It does **not** do advanced ontology merging across every weird biomedical synonym.
- It does **not** store runs in a database yet.
- It assumes PubTator returns a compatible BioC JSON structure for the export endpoint.

That is fine. The goal of v1 is to be clear, useful, and shippable.

---

## Possible next upgrades

Once the project is stable, the next logical upgrades are:

- side-by-side query comparison
- journal filters
- year sliders
- subgraph export
- centrality metrics
- community detection
- SQLite or Postgres persistence
- background job queue for bigger literature pulls
- report export for a chosen topic

---

## Resume bullets you can pull from this

- Built a biomedical literature mining application that converts PubMed search results into interactive knowledge graphs using PubTator annotations.
- Implemented a Python pipeline for metadata retrieval, biomedical entity parsing, normalization-aware graph construction, and exportable CSV/JSON outputs.
- Designed a custom Flask front end for exploring gene–disease–chemical–variant relationships, publication timelines, and supporting evidence across the literature.

---

## Notes on the bundled demo

The included demo dataset is a **small synthetic sample** inspired by the EGFR/NSCLC literature. It exists so the UI and graph logic can be tested instantly without depending on live external services.


## Desktop packaging (.exe and .app)

BioLitGraph includes a desktop launcher so you can package it as a clickable app.

### Windows build

```bat
build_windows.bat
```

This creates:

```text
dist\BioLitGraph\BioLitGraph.exe
```

### macOS build

```bash
./build_macos.sh
```

This creates:

```text
dist/BioLitGraph.app
```

### Where packaged runs are saved

Packaged builds store outputs in a user-writable folder instead of inside the app bundle:

- **Windows:** `%LOCALAPPDATA%\BioLitGraph`
- **macOS:** `~/Library/Application Support/BioLitGraph`
- **Linux:** `~/.local/share/BioLitGraph`
