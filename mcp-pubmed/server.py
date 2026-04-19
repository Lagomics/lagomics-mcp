import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("pubmed")
BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


@mcp.tool()
def search_pubmed(query: str, max_results: int = 10) -> list[dict]:
    """Search PubMed articles. Returns PMID, title, authors, and publication date."""
    r = requests.get(f"{BASE}/esearch.fcgi", params={
        "db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"
    })
    ids = r.json()["esearchresult"]["idlist"]
    if not ids:
        return []

    r2 = requests.get(f"{BASE}/esummary.fcgi", params={
        "db": "pubmed", "id": ",".join(ids), "retmode": "json"
    })
    result = r2.json()["result"]
    return [
        {
            "pmid": pid,
            "title": result[pid]["title"],
            "authors": [a["name"] for a in result[pid].get("authors", [])[:5]],
            "pubdate": result[pid]["pubdate"],
            "journal": result[pid]["fulljournalname"],
        }
        for pid in ids if pid in result
    ]


@mcp.tool()
def get_abstract(pmid: str) -> str:
    """Fetch the full abstract for a PubMed article by PMID."""
    r = requests.get(f"{BASE}/efetch.fcgi", params={
        "db": "pubmed", "id": pmid, "rettype": "abstract", "retmode": "text"
    })
    return r.text.strip()


@mcp.tool()
def get_related_articles(pmid: str, max_results: int = 5) -> list[dict]:
    """Find PubMed articles related to a given PMID, ranked by similarity."""
    r = requests.get(f"{BASE}/elink.fcgi", params={
        "dbfrom": "pubmed", "db": "pubmed", "id": pmid,
        "retmode": "json", "cmd": "neighbor_score"
    })
    data = r.json()
    try:
        links = data["linksets"][0]["linksetdbs"][0]["links"]
        ids = [str(l) for l in links[:max_results]]
    except (KeyError, IndexError):
        return []

    r2 = requests.get(f"{BASE}/esummary.fcgi", params={
        "db": "pubmed", "id": ",".join(ids), "retmode": "json"
    })
    result = r2.json()["result"]
    return [
        {"pmid": pid, "title": result[pid]["title"], "pubdate": result[pid]["pubdate"]}
        for pid in ids if pid in result
    ]


mcp.run()
