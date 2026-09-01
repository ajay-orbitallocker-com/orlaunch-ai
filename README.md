# ORLaunch AI - Hybrid RAG + GPT-4o Mini MVP

## 🎯 Project Objective
Allow multiple team members to work independently while maintaining a stable integration environment. All work must flow through **develop** before reaching **main**.

## 🚀 Project Strategy

### 1. Repository Branch Structure
- **main**: Stable / Production branch.
- **develop**: Integration branch.
- **feature/**: Dedicated branches for specific domains.

### 2. Branch Ownership & Domains
- **feature/rag-sources**: Knowledge Base & Data Strategy
- **feature/rag-engine**: RAG Engineering & Retrieval
- **feature/gpt-analysis**: GPT Integration & Prompt Engineering
- **feature/architecture**: Architecture, Integration & Reviews

## 📁 Directory Structure
- `chroma_config.py`: ChromaDB client/collection setup and OpenAI client config.
- `main.py`: Sample entry point comparing broad vs. category-filtered retrieval on a hardcoded idea.
- `docs/`: Documentation and architecture maps.
- `data/`: Raw and processed knowledge base data.
- `rag/`: RAG pipeline (ingestion, embeddings, retrieval, evaluation).
  - `ingestion/`: Fetches, filters, and chunks documents from all data sources.
    - `sources/rss_market/`: SpaceNews/Payload RSS market news fetcher.
    - `sources/sec_edgar/`: SEC EDGAR financial benchmark fetcher.
    - `sources/techport/`: NASA TechPort project fetcher.
    - `sources/patents/`: USPTO/patent prior-art fetcher.
    - `ingest_all.py`: Orchestrates all 4 sources into chunk -> embed -> store.
  - `embeddings/`: Batch embedding generation and writing chunks to ChromaDB.
  - `retrieval/`: Query embedding + top-K similarity search against ChromaDB (`search.py`), plus retrieval evaluation (`evaluate.py`).
  - `retrieval_eval/`: Retrieval quality evaluation suite - LLM-judged relevance fixtures (`generate_relevance_judgments.py`, `fixtures/`) scored against live retrieval with IR metrics (`metrics.py`: recall, precision, MRR, NDCG, MAP, context precision/recall).
  - `hallucination/`: Post-generation hallucination checking - citation coverage (`citation_check.py`), LLM-judged faithfulness (`faithfulness.py`), and combined reporting (`report.py`), evaluated against a mock CDD (`evaluate_hallucination.py`).
- `ai/`: GPT logic, prompt templates, and data schemas.
  - `prompts/`: AI prompt templates (grounded and inference section prompts).
  - `gpt/`: Core GPT integration logic - CDD section generation (`generate_cdd.py`) and PDF export (`pdf_export.py`).
  - `schemas/`: Pydantic schemas for each CDD section and generation-output validation (`cdd_schema.py`).
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
    python -m ai.gpt.generate_cdd