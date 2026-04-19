import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("alphafold")
BASE = "https://alphafold.ebi.ac.uk/api"


@mcp.tool()
def get_prediction(uniprot_accession: str) -> dict:
    """
    Get AlphaFold structure prediction metadata for a UniProt accession.
    Returns confidence scores, model version, and download URLs.
    """
    r = requests.get(f"{BASE}/prediction/{uniprot_accession}")
    if r.status_code == 404:
        return {"error": f"No AlphaFold prediction found for {uniprot_accession}"}

    entries = r.json()
    if not entries:
        return {"error": "No predictions returned"}

    e = entries[0]
    return {
        "accession": e.get("uniprotAccession"),
        "entry_id": e.get("entryId"),
        "gene": e.get("gene"),
        "protein_name": e.get("uniprotDescription"),
        "organism": e.get("organismScientificName"),
        "sequence_length": e.get("sequenceLength"),
        "model_version": e.get("latestVersion"),
        "mean_plddt": e.get("globalMetricValue"),  # mean confidence score 0-100
        "pdb_url": e.get("pdbUrl"),
        "cif_url": e.get("cifUrl"),
        "pae_image_url": e.get("paeImageUrl"),
        "plddt_json_url": e.get("plddtDocUrl"),
    }


@mcp.tool()
def search_alphafold(gene_name: str, organism: str = "Homo sapiens") -> list[dict]:
    """
    Find AlphaFold predictions by gene name and organism.
    First queries UniProt to resolve the accession, then fetches AlphaFold data.
    """
    # Resolve gene → UniProt accession
    query = f"gene:{gene_name} AND organism_name:{organism} AND reviewed:true"
    r = requests.get("https://rest.uniprot.org/uniprotkb/search", params={
        "query": query, "format": "json", "size": 5,
        "fields": "accession,protein_name,gene_names,length"
    })
    hits = r.json().get("results", [])
    if not hits:
        return [{"error": f"No UniProt entries found for gene {gene_name} in {organism}"}]

    results = []
    for hit in hits:
        accession = hit["primaryAccession"]
        af = requests.get(f"{BASE}/prediction/{accession}")
        if af.status_code != 200 or not af.json():
            continue
        e = af.json()[0]
        results.append({
            "accession": accession,
            "gene": e.get("gene"),
            "protein_name": e.get("uniprotDescription"),
            "sequence_length": e.get("sequenceLength"),
            "mean_plddt": e.get("globalMetricValue"),
            "pdb_url": e.get("pdbUrl"),
        })
    return results


mcp.run()
