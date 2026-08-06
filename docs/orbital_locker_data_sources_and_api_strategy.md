# Orbital Locker – Data Sources, Public APIs & Scraping Blueprint

**Project:** Orbital Locker / ORLaunch AI (Hybrid RAG + GPT-4o Mini MVP)  
**Author:** Ajay Kumar Avula (RAG Engineering & Retrieval Lead)  
**Target:** Keith Samba (AI Lead & Solution Architect) & Team  

---

## Executive Summary

To power the **Hybrid RAG + GPT-4o Mini pipeline** for automated space/aerospace startup analysis, we have conducted an extensive evaluation of the 26 SME-provided data sources and expanded them with public REST APIs across **Technical & TRL**, **Market Intelligence**, **Financial Intelligence**, **Patents & IP**, and **Startup Intelligence**.

This document outlines:
1. **API Identification & Data Scraping Strategy** for each category.
2. **Scope Analysis of Public Data vs. Missing/Unreachable Data**.
3. **Engineered Data Ingestion Architecture & Next Development Steps**.

---

## 1. Categorized Data Sources & API / Scraping Inventory

### A. Technical & TRL Data Sources

| Source | Public API Status | Endpoint / Access Method | Data Format | Ingestion Target |
|---|---|---|---|---|
| **NASA TechPort** | ✅ **Active Public REST API** | `https://techport.nasa.gov/api/projects/search` | JSON | Project title, TRL current/start/target, taxonomy codes (TX01, TX04, TX10, TX17), description, benefits |
| **NASA STI (NTRS)** | ✅ **Active Public REST API** | `https://ntrs.nasa.gov/api/citations/search` | JSON | NASA Technical Reports, conference papers, mission feasibility studies |
| **ESA BIC & JAXA Startups** | ⚠️ **Web Scraping Required** | `BeautifulSoup` scraping of `esa.int` & `aerospacebiz.jaxa.jp` | HTML -> Text | Incubated startup descriptions, technology domain keywords, mission profiles |
| **ArXiv Aerospace / Engineering** | ✅ **Active Public REST API** | `http://export.arxiv.org/api/query?searchquery=cat:astro-ph` | XML / JSON | Academic preprints, CubeSat subsystem research, propulsion models |

### B. Financial Intelligence Data Sources

| Source | Public API Status | Endpoint / Access Method | Data Format | Ingestion Target |
|---|---|---|---|---|
| **SEC EDGAR API** | ✅ **Free Public REST API** | `https://data.sec.gov/api/xbrl/companyfacts/` | JSON / XBRL | Public space company financials (Planet Labs, Rocket Lab, Spire Global, Intuitive Machines). Covers R&D expenditure, Gross Margin, Cash Flow, Financial Risks |
| **Yahoo Finance API (`yfinance`)** | ✅ **Free Python SDK / REST** | `yfinance` library | JSON / DataFrames | Valuation multiples (P/S, EV/Revenue), market caps, sector financial ratios in aerospace & defense |
| **Financial Modeling Prep (FMP)** | ⚠️ **Free Tier API Available** | `https://financialmodelingprep.com/api/v3/` | JSON | Financial statements, key ratios, benchmark cost metrics |

### C. Market Intelligence & Sector News

| Source | Public API Status | Endpoint / Access Method | Data Format | Ingestion Target |
|---|---|---|---|---|
| **Launch Library 2 (TheSpaceDevs)** | ✅ **Free Public REST API** | `https://ll.thespacedevs.com/2.2.0/launch/` | JSON | Launch manifests, satellite payload specs, orbit types (LEO, GEO, SSO), launch costs |
| **Space-Track API** | ✅ **Free Public REST API** | `https://www.space-track.org/basicapi/query` | JSON | Orbital catalog (TLE data), satellite decay rates, space debris density metrics |
| **Payload Space / SpaceNews / TechCrunch** | ⚠️ **RSS Feed + Scraper** | RSS Feeds (`/feed`) + `feedparser` / `BeautifulSoup` | XML / HTML | Industry trends, funding announcements, regulatory policy shifts, market sizing quotes |

### D. Patents & Subsystem Prior Art

| Source | Public API Status | Endpoint / Access Method | Data Format | Ingestion Target |
|---|---|---|---|---|
| **USPTO PatentsView API** | ✅ **Free Public REST API** | `https://api.patentsview.org/patents/query` | JSON | Subsystem patent claims, CPC codes, patent abstracts, assignee info |
| **Google Patents** | ⚠️ **BigQuery / Scraping** | BigQuery `patents-public-data` or `BeautifulSoup` | JSON / Text | Patent text, subsystem block diagrams, IPC classification |
| **WIPO Patentscope API** | ✅ **Free REST API** | `https://www me.wipo.int/patentscope-api/` | JSON | International patent applications (PCT) for propulsion, optics, ground control |

### E. Startup Intelligence & Directories

| Source | Public API Status | Endpoint / Access Method | Data Format | Ingestion Target |
|---|---|---|---|---|
| **Crunchbase / F6S / AngelList** | ❌ **Paid / Gated API** | Web Scraping (`Playwright` / `BeautifulSoup`) | HTML | Company summaries, funding round history, tag taxonomies |
| **SpaceFund Startup Tracker** | ⚠️ **Web Scraper** | `BeautifulSoup` on `spacefund.com` tracker | HTML Table | Curated space startup database categorized by sector (launch, satellite, servicing) |

---

## 2. Scope Analysis: Public Data Scope vs. Missing/Unreachable Data

```
+-------------------------------------------------------------------------------+
|                             DATA AVAILABILITY MATRIX                          |
+------------------------------------+------------------------------------------+
|  CAN FETCH VIA PUBLIC APIs          |  MISSING / UNABLE TO FETCH               |
+------------------------------------+------------------------------------------+
| • NASA TechPort R&D & TRL Scores   | • Early-stage private startup financials |
| • SEC EDGAR R&D & SEC 10-K Data    |   (Valuations, Cap tables, Burn rates)   |
| • USPTO Patent prior art & claims  | • Paywalled analyst reports (BryceTech,  |
| • Launch Library 2 payload specs   |   Euroconsult $5K+ market reports)       |
| • Industry RSS news & launches     | • Full-text ProQuest dissertations       |
| • ArXiv preprints & academic papers|   (Behind university Shibboleth/SSO)     |
+------------------------------------+------------------------------------------+
```

### Key Limitations & Mitigation Strategies
1. **Private Financial Data Gap:** Early-stage space startups do not disclose balance sheets publicly.  
   *Mitigation:* Use public benchmark space companies from SEC EDGAR (e.g., Planet Labs `CIK: 0001836833`, Rocket Lab `CIK: 0001819974`) to build sector cost models and R&D ratio heuristics.
2. **Crunchbase / PitchBook Paywall:** Direct API access costs $10,000+/yr.  
   *Mitigation:* Scrape open startup listings (F6S, SpaceFund Tracker) and augment with NASA TechPort and SEC filings.

---

## 3. Recommended Technical Ingestion Architecture

To integrate these data sources into our ChromaDB vector store:

```
[ Public APIs / Web Scrapers ]
  ├── NASA TechPort API (Tech & TRL)
  ├── SEC EDGAR API (Financial Benchmarks)
  ├── USPTO PatentsView API (Prior Art)
  └── SpaceNews / Payload RSS (Market Intelligence)
               │
               ▼
[ Python Ingestion Modules (rag/ingestion/) ]
  ├── fetch_all_projects.py (TechPort)
  ├── sec_edgar.py (Financials)
  ├── patents.py (USPTO)
  └── rss_market.py (News/Market)
               │
               ▼
[ Cleaning & Token Chunking (chunk.py) ]
               │ (cl100k_base 500 tokens / 100 overlap)
               ▼
[ OpenAI Batch Embedding API ]
               │ (text-embedding-3-small)
               ▼
[ ChromaDB Vector Storage (src/data/chromadb) ]
               │
               ▼
[ GPT-4o Mini Context Package ]
```

---

## 4. Next Development Steps for Ajay (RAG Engineering & Retrieval Lead)

1. **Build `sec_edgar.py`**: Fetch SEC 10-K financial metrics and R&D budgets for key aerospace benchmarks.
2. **Build `rss_market.py`**: Ingest latest space market news via RSS feeds to provide fresh market context.
3. **Build `patents.py`**: Fetch subsystem patent abstracts for satellite and propulsion technology.
4. **Update `embed_and_store.py`**: Extend ChromaDB metadata schema to support multi-category search (`category="technical"`, `category="financial"`, `category="market"`).
