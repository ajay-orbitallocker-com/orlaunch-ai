# ORLaunch AI - Hybrid RAG + GPT-4o Mini MVP

## Project Objective
Allow multiple team members to work independently while maintaining a stable integration environment. All work must flow through **develop** before reaching **main**.

## Project Strategy

### 1. Repository Branch Structure
- **main**: Stable / Production branch.
- **develop**: Integration branch.
- **feature/**: Dedicated branches for specific domains.

### 2. Branch Ownership & Domains
- **feature/rag-sources**: Knowledge Base & Data Strategy
- **feature/rag-engine**: RAG Engineering & Retrieval
- **feature/gpt-analysis**: GPT Integration & Prompt Engineering
- **feature/architecture**: Architecture, Integration & Reviews

## Directory Structure
- `chroma_config.py`: ChromaDB client/collection setup and OpenAI client config.
- `main.py`: Sample entry point comparing broad vs. category-filtered retrieval on a hardcoded idea.
- `docs/`: Documentation and architecture maps.
- `data/`: Raw and processed knowledge base data.
- `rag/`: RAG pipeline (ingestion, embeddings, retrieval, evaluation).
  - `ingestion/`: Fetches, filters, and chunks documents from all data sources.
    - `sources/rss_market/`: SpaceNews/Payload RSS market news fetcher.
    - `sources/sec_edgar/`: SEC EDGAR financial benchmark fetcher.
    - `sources/techport/`: NASA TechPort project fetcher.
    - `sources/patents/`: NASA STI (NTRS) prior-art fetcher.
    - `ingest_all.py`: Orchestrates all 4 sources into chunk -> embed -> store.
  - `embeddings/`: Batch embedding generation and writing chunks to ChromaDB.
  - `retrieval/`: Query embedding + top-K similarity search against ChromaDB (`search.py`), plus retrieval evaluation (`evaluate.py`).
  - `retrieval_eval/`: Retrieval quality evaluation suite - LLM-judged relevance fixtures (`generate_relevance_judgments.py`, `fixtures/`) scored against live retrieval with IR metrics (`metrics.py`: recall, precision, MRR, NDCG, MAP, context precision/recall).
  - `hallucination/`: Post-generation hallucination checking - citation coverage (`citation_check.py`), LLM-judged faithfulness (`faithfulness.py`), and combined reporting (`report.py`), evaluated against a mock CDD (`evaluate_hallucination.py`).
- `ai/`: CDD generation - template selection, outline planning, section generation and PDF export.
  - `templates/`: Decides which sections a CDD must have (pure code, no LLM calls).
    - `template_labels.py`: The five label enums (Segment, Domain, OfferingType, FundingPath, Audience).
    - `template_selection.py`: Label selection models; Segment, Domain and FundingPath take a primary plus optional secondary values.
    - `template_label_conditions.py`: Yes/no facts derived from the labels (commercial, hardware, science, etc.).
    - `template_sections.py`: The catalogue of stable section ids.
    - `template_section_rules.py`: When each section is included (always, requires or excludes a condition) and the exclusive section pairs.
    - `template_section_details.py`: Per section a fallback heading, its purpose, GROUNDED/INFERENCE, and whether it is written from other sections.
    - `template_label_guide.py`: Meaning of each label value, used in the labelling prompt.
    - `build_template.py`: Labels -> guaranteed sections (the floor every CDD gets).
    - `check_cdd_outline.py`: Enforces the template's rules on the AI-planned outline and fixes what it safely can.
    - `config.py`: Limits for extra sections and heading length.
  - `gpt/`: The generation pipeline and LLM calls.
    - `run_cdd_pipeline.py`: Runs the full pipeline: validate idea -> select labels -> build template -> plan outline -> generate -> check structure.
    - `validate_idea.py`: Query-routing gate that rejects input that is not a venture idea.
    - `select_template.py`: AI picks the template labels from the idea.
    - `plan_cdd_outline.py`: AI plans the outline (assessments, extra sections, order, headings), checked and retried on failure.
    - `generate_cdd.py`: Writes every outline section (grounded, inference or written from other sections).
    - `section_inputs.py`: Per section prompt name, output schema, section brief and retrieval queries.
    - `retrieve_cdd_sources.py`: Retrieves documents for sections and gives each one [Doc N] number.
    - `check_cdd_structure.py`: Checks every section was written and citation numbers line up.
    - `llm.py`: Shared structured-output LLM call.
    - `pdf_export.py`: Exports the CDD to PDF with linked citations and a References list.
    - `config.py`: Model names, top-k and retry limits.
  - `prompts/`: Prompt builders.
    - `cdd_prompts.py`: Grounded, inference, synthesis and query-routing prompts.
    - `template_prompts.py`: Labelling prompt.
    - `outline_prompts.py`: Outline-planning prompt.
  - `schemas/`: Pydantic schemas.
    - `cdd_schema.py`: Output schema for each CDD section.
    - `template_selection_schema.py`: AI labelling result (labels, project name, confidence).
    - `outline_schema.py`: The planned outline and its sections.
- `tests/`: Unit and integration tests.
- `outputs/`: Generated reports and logs.

## Setup

1. Clone the repo
2. Create and activate a virtual environment:
    python -m venv venv
    venv\Scripts\activate # Windows
    source venv/bin/activate # Mac/Linux
3. Install dependencies:
    pip install -r requirements.txt
4. Create a `.env` file in the project root with:
    OPENAI_API_KEY=your_key_here
5. Run ingestion (fetches all 4 sources, chunks, embeds, and stores into the local ChromaDB collection):
    python -m rag.ingestion.ingest_all
6. Generate a sample CDD from the populated collection:
    python -m ai.gpt.run_cdd_pipeline