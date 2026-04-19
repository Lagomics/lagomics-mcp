import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("uniprot")
BASE = "https://rest.uniprot.org/uniprotkb"


@mcp.tool()
def search_proteins(query: str, max_results: int = 10) -> list[dict]:
    """Search UniProt for proteins by name, gene, function, or organism."""
    r = requests.get(f"{BASE}/search", params={
        "query": query,
        "format": "json",
        "size": max_results,
        "fields": "accession,protein_name,gene_names,organism_name,length,reviewed"
    })
    entries = r.json().get("results", [])
    return [
        {
            "accession": e["primaryAccession"],
            "name": e.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "N/A"),
            "gene": e.get("genes", [{}])[0].get("geneName", {}).get("value", "N/A") if e.get("genes") else "N/A",
            "organism": e.get("organism", {}).get("scientificName", "N/A"),
            "length": e.get("sequence", {}).get("length", "N/A"),
            "reviewed": e.get("entryType") == "UniProtKB reviewed (Swiss-Prot)",
        }
        for e in entries
    ]


@mcp.tool()
def get_protein(accession: str) -> dict:
    """Get full protein details from UniProt by accession (e.g. P53_HUMAN → TP53)."""
    r = requests.get(f"{BASE}/{accession}", params={"format": "json"})
    e = r.json()

    comments = {
        c["commentType"]: c
        for c in e.get("comments", [])
        if "commentType" in c
    }

    function_text = "N/A"
    if "FUNCTION" in comments:
        texts = comments["FUNCTION"].get("texts", [])
        if texts:
            function_text = texts[0].get("value", "N/A")

    subcell = "N/A"
    if "SUBCELLULAR LOCATION" in comments:
        locs = comments["SUBCELLULAR LOCATION"].get("subcellularLocations", [])
        subcell = ", ".join(
            l.get("location", {}).get("value", "") for l in locs
        )

    return {
        "accession": e["primaryAccession"],
        "name": e.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "N/A"),
        "gene": e.get("genes", [{}])[0].get("geneName", {}).get("value", "N/A") if e.get("genes") else "N/A",
        "organism": e.get("organism", {}).get("scientificName", "N/A"),
        "length": e.get("sequence", {}).get("length", "N/A"),
        "function": function_text,
        "subcellular_location": subcell,
        "reviewed": e.get("entryType") == "UniProtKB reviewed (Swiss-Prot)",
    }


@mcp.tool()
def get_protein_sequence(accession: str) -> str:
    """Get the FASTA sequence for a UniProt accession."""
    r = requests.get(f"{BASE}/{accession}", params={"format": "fasta"})
    return r.text.strip()


mcp.run()
