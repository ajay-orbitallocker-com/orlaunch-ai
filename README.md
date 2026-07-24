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
- `docs/`: Documentation and architecture maps.
- `data/`: Raw and processed knowledge base data.
- `rag/`: RAG pipeline (ingestion, embeddings, retrieval).
- `ai/`: GPT logic, prompt templates, and data schemas.
  - `prompts/`: AI prompt templates.
  - `gpt/`: Core GPT integration logic.
  - `schemas/`: Data models and validation schemas.
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
5. Run ingestion:
    python -m src.embeddings.embed_and_store