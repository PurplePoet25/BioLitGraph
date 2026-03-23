# BioLitGraph

**BioLitGraph** is a local biomedical literature mining tool that turns PubMed search results into an interactive knowledge graph.

You enter a biomedical topic such as:

- `BRCA1 AND breast cancer`
- `TP53 AND acute myeloid leukemia`
- `(EGFR OR ERBB1) AND "non-small cell lung cancer"`

BioLitGraph then:

1. searches PubMed for relevant papers  
2. collects paper metadata  
3. retrieves biomedical annotations from PubTator  
4. extracts normalized entities such as genes, diseases, chemicals, and variants  
5. builds an interactive graph showing how those entities connect across the literature  

The result is a faster, more visual way to explore a topic before diving deep into individual papers.

---

## Why this project exists

Biomedical literature is huge, messy, and hard to scan quickly.

Normally, exploring a topic means opening dozens of papers, skimming titles and abstracts, writing down repeated concepts, and slowly building a mental map of the field.

BioLitGraph helps with that first step.

It does **not** replace reading papers. It helps you understand the **shape of a topic** before you go deeper.

In simple terms, BioLitGraph answers a question like:

> **If I search a biomedical topic, what genes, diseases, drugs, and variants keep showing up together across the literature?**

That makes it useful for:
- quick literature exploration
- early-stage hypothesis building
- topic familiarization
- teaching and demos
- portfolio demonstration of biomedical NLP, graph analytics, and data engineering

---

## What the app does

For a single topic query, BioLitGraph can:

- search PubMed for the top relevant papers
- collect paper metadata such as PMID, title, journal, and publication date
- fetch PubTator annotations for those PMIDs
- extract **genes, diseases, chemicals, variants, and cell lines**
- collapse repeated mentions into normalized entities
- build a graph where nodes are entities and edges are connections supported by papers
- show top entities, top edges, a publication timeline, a paper table, and a click-to-inspect graph
- save each run as CSV and JSON outputs

The project also includes a **bundled demo mode**, so the full UI can be tested even when live APIs are unavailable.

---

## How it works

BioLitGraph is built in four main layers.

### 1. Retrieval layer

The user enters a biomedical topic.

BioLitGraph sends that query to **PubMed** using NCBI E-utilities. PubMed returns a set of relevant paper IDs (PMIDs), and the app then fetches summary metadata such as titles, journals, and dates.

This layer answers:

- Which papers are most relevant to this topic?
- What basic information do we want to store for each paper?

### 2. Annotation layer

Once BioLitGraph has PMIDs, it sends them to **PubTator**.

PubTator is a biomedical text-mining system that marks important entities inside papers. These entities can include:

- genes
- diseases
- chemicals
- variants
- cell lines

PubTator also provides normalized identifiers when possible, which helps the app treat repeated mentions as the same concept.

This layer answers:

- What biological concepts appear in these papers?
- Which mentions refer to the same underlying entity?

### 3. Graph layer

After entity extraction, BioLitGraph converts the results into a network.

- **Nodes** represent biological entities
- **Edges** represent connections between entities

An edge can come from:
- a direct extracted relation from PubTator, or
- co-occurrence within the same paper

Edge weights are based on supporting papers, so stronger recurring connections become more visible.

This layer answers:

- Which concepts are central in the topic?
- Which concepts frequently appear together?
- What clusters or neighborhoods appear in the literature?

### 4. Interface layer

The final step is presenting the results in a way that is useful.

The app displays:
- an interactive graph
- top entities by type
- top edges by support
- a publication timeline
- a paper table
- details for selected nodes and edges

This makes the literature feel less like a wall of text and more like an explorable map.

---

## What kinds of queries work best

The strongest queries are usually **focused biomedical combinations**, not overly broad terms.

### Good query patterns

- **gene + disease**  
  `BRCA1 AND breast cancer`

- **drug + gene + disease**  
  `(gefitinib OR erlotinib) AND EGFR AND "non-small cell lung cancer"`

- **disease + pathogen**  
  `"cystic fibrosis" AND "Pseudomonas aeruginosa"`

- **small gene family + disease**  
  `(APOE OR APP OR PSEN1) AND "Alzheimer disease"`

These work well because they tend to produce coherent literature clusters with recognizable biological entities.

### Weaker query patterns

Very broad queries can create noisy graphs, such as:

- `cancer`
- `aging`
- `food AND microbes`
- `preservatives AND industry`

These are still valid, but they often produce generic high-frequency terms and weaker graph structure.

### Query tips

- Use `AND` for focused combinations
- Use `OR` for close synonyms
- Use quotes for multi-word phrases
- Be careful with `NOT`, since it can remove useful papers too aggressively

---

## Example queries

Try these first:

```text
BRCA1 AND breast cancer
TP53 AND acute myeloid leukemia
(EGFR OR ERBB1) AND "non-small cell lung cancer"
(gefitinib OR erlotinib) AND EGFR AND "non-small cell lung cancer"
(APOE OR APP OR PSEN1) AND "Alzheimer disease"
"cystic fibrosis" AND "Pseudomonas aeruginosa"
(telomeres OR telomerase) AND aging
```

---

## Demo mode

BioLitGraph ships with demo data so the interface can be tested immediately.

Use demo mode when:
- you want to verify the UI quickly
- live API access is unavailable
- you want a reliable example for screenshots or presentations

---

## Tech stack

- **Python**
- **Flask**
- **Waitress**
- **PubMed E-utilities**
- **PubTator**
- **pandas**
- **NetworkX**
- **vis-network / front-end graph rendering**
- **HTML, CSS, JavaScript**

---

## Repository structure

```text
BioLitGraph/
├── app.py
├── launcher.py
├── src/
│   ├── clients/
│   ├── graph_builder.py
│   ├── pipeline.py
│   ├── parsers.py
│   └── utils.py
├── templates/
├── static/
├── data/
│   ├── demo/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── outputs/
│   └── runs/
├── tests/
├── assets/
├── README.md
├── requirements.txt
├── requirements-build.txt
├── build_windows.bat
├── build_macos.sh
└── BioLitGraph.spec
```

---

## Installation

### Windows

```bat
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
python -m flask --app app run
```

Then open:

```text
http://127.0.0.1:5000
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m flask --app app run
```

Then open:

```text
http://127.0.0.1:5000
```

---

## Packaged desktop builds

BioLitGraph can also be packaged as a local desktop app.

### Build Windows executable

```bat
build_windows.bat
```

### Build macOS app bundle

```bash
chmod +x build_macos.sh
./build_macos.sh
```

Packaged builds use a local server with **Waitress** and automatically open in the browser.

---

## Outputs

Each run can generate structured outputs such as:

- paper metadata tables
- extracted entity tables
- edge tables
- JSON summaries

These outputs make the project useful both as an interactive app and as a reproducible data-processing pipeline.

---

## What this project demonstrates

BioLitGraph was designed to show more than front-end polish.

It demonstrates:

- biomedical API integration
- biomedical NLP workflow design
- entity normalization
- graph construction and filtering
- scientific data modeling
- local web app packaging
- practical thinking about noisy real-world data

---

## Limitations

BioLitGraph is a literature exploration tool, not a truth machine.

A few important limitations:

- it depends on external APIs
- broad or vague queries can still produce noisy results
- entity extraction quality depends on PubTator output
- co-occurrence does **not** automatically mean biological causation
- the tool is meant to support reading and exploration, not replace scientific interpretation

---

## Future improvements

Planned or possible next steps include:

- filtering by year
- filtering by entity type
- richer node and edge inspection
- exportable snapshots or reports
- stronger abbreviation handling
- better edge-type explanations
- multi-query comparison

---

## Resume-style summary

> Built a biomedical literature mining pipeline that retrieves PubMed papers, extracts normalized biological entities using PubTator, and converts them into interactive knowledge graphs for topic exploration.



- **macOS:** `~/Library/Application Support/BioLitGraph`
- **Linux:** `~/.local/share/BioLitGraph`
