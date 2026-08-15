import requests
import json

SEC_HEADERS = {
    "User-Agent": "OrbitalLocker/1.0 (ajaykumaravula999@gmail.com)"
}

SPACE_BENCHMARKS = [
    {"name": "Northrop Grumman Corp", "cik": "0000072971", "symbol": "NOC"},
    {"name": "Lockheed Martin Corp", "cik": "0000936468", "symbol": "LMT"},
    {"name": "Rocket Lab USA Inc", "cik": "0001819974", "symbol": "RKLB"},
    {"name": "Planet Labs PBC", "cik": "0001836833", "symbol": "PL"}
]

def fetch_sec_company_facts(cik: str) -> dict:
    """Fetch company facts from SEC EDGAR API."""
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik.zfill(10)}.json"
    response = requests.get(url, headers=SEC_HEADERS)
    response.raise_for_status()
    return response.json()

def extract_financial_summary(company_info: dict, cik: str) -> dict:
    """Extract key financial metrics (Revenues, R&D Expense, Net Income) for RAG context."""
    raw_data = fetch_sec_company_facts(cik)
    entity_name = raw_data.get("entityName", company_info["name"])
    gaap_facts = raw_data.get("facts", {}).get("us-gaap", {})
    
    extracted = {
        "company": entity_name,
        "symbol": company_info["symbol"],
        "cik": cik,
        "metrics": {}
    }
    
    target_metrics = [
        "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
        "ResearchAndDevelopmentExpense", "GrossProfit", "NetIncomeLoss"
    ]
    
    for metric_key in target_metrics:
        if metric_key in gaap_facts:
            metric_data = gaap_facts[metric_key]
            units = metric_data.get("units", {})
            for unit_key, records in units.items():
                if records:
                    recent = sorted(records, key=lambda x: x.get("end", ""))[-1]
                    extracted["metrics"][metric_key] = {
                        "label": metric_data.get("label"),
                        "val": recent.get("val"),
                        "fy": recent.get("fy"),
                        "form": recent.get("form")
                    }
                    break
                    
    return extracted

def build_sec_document_text(financial_data: dict) -> str:
    """Format extracted financial data into clean text for vector embeddings."""
    lines = [
        f"Company: {financial_data['company']} (Ticker: {financial_data['symbol']})",
        "Category: Financial Intelligence & Sector Benchmarks",
        "Source: SEC EDGAR 10-K/10-Q Public Filings",
        "Financial Highlights:"
    ]
    for m_key, m_val in financial_data.get("metrics", {}).items():
        lines.append(f" - {m_val['label']} ({m_val.get('fy', 'N/A')}): ${m_val['val']:,} USD [Form {m_val.get('form', '10-K')}]")
        
    return "\n".join(lines)

def fetch_all_financial_benchmarks() -> list[dict]:
    """Fetch financial benchmarks for all space companies."""
    results = []
    for comp in SPACE_BENCHMARKS:
        try:
            summary = extract_financial_summary(comp, comp["cik"])
            doc_text = build_sec_document_text(summary)
            results.append({
                "source_id": f"SEC_{comp['cik']}",
                "title": f"Financial Benchmark: {comp['name']} ({comp['symbol']})",
                "text": doc_text,
                "category": "Financial Intelligence",
                "source": "SEC EDGAR",
                "url": f"https://www.sec.gov/edgar/browse/?CIK={comp['cik']}"
            })
        except Exception as e:
            print(f"Error fetching SEC data for {comp['name']}: {e}")
    return results

if __name__ == "__main__":
    benchmarks = fetch_all_financial_benchmarks()
    print(f"Successfully fetched {len(benchmarks)} financial benchmark documents.")
    if benchmarks:
        print("Sample SEC Document:\n", benchmarks[0]["text"])
