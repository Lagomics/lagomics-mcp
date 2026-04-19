"""
Lagomics MCP — combined SSE server
All Tier 1 biotech tools in one process, served over HTTP/SSE for remote use.
Run locally:  python server.py
On Render:    auto-started via render.yaml
Connect via:  https://<your-render-url>/sse
"""
import os
import re
import json
import time
import requests
from mcp.server.fastmcp import FastMCP

port = int(os.environ.get("PORT", 8000))
mcp = FastMCP("lagomics-biotech", host="0.0.0.0", port=port)

# ─────────────────────────────────────────────
# PubMed
# ─────────────────────────────────────────────
PUBMED = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


@mcp.tool()
def pubmed_search(query: str, max_results: int = 10) -> list[dict]:
    """Search PubMed articles. Returns PMID, title, authors, journal, and date."""
    r = requests.get(f"{PUBMED}/esearch.fcgi", params={
        "db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"
    })
    ids = r.json()["esearchresult"]["idlist"]
    if not ids:
        return []
    r2 = requests.get(f"{PUBMED}/esummary.fcgi", params={
        "db": "pubmed", "id": ",".join(ids), "retmode": "json"
    })
    result = r2.json()["result"]
    return [
        {
            "pmid": pid,
            "title": result[pid]["title"],
            "authors": [a["name"] for a in result[pid].get("authors", [])[:5]],
            "journal": result[pid]["fulljournalname"],
            "pubdate": result[pid]["pubdate"],
        }
        for pid in ids if pid in result
    ]


@mcp.tool()
def pubmed_abstract(pmid: str) -> str:
    """Fetch the full abstract for a PubMed article by PMID."""
    r = requests.get(f"{PUBMED}/efetch.fcgi", params={
        "db": "pubmed", "id": pmid, "rettype": "abstract", "retmode": "text"
    })
    return r.text.strip()


@mcp.tool()
def pubmed_related(pmid: str, max_results: int = 5) -> list[dict]:
    """Find PubMed articles related to a given PMID, ranked by similarity."""
    r = requests.get(f"{PUBMED}/elink.fcgi", params={
        "dbfrom": "pubmed", "db": "pubmed", "id": pmid,
        "retmode": "json", "cmd": "neighbor_score"
    })
    try:
        ids = [str(l) for l in r.json()["linksets"][0]["linksetdbs"][0]["links"][:max_results]]
    except (KeyError, IndexError):
        return []
    r2 = requests.get(f"{PUBMED}/esummary.fcgi", params={
        "db": "pubmed", "id": ",".join(ids), "retmode": "json"
    })
    result = r2.json()["result"]
    return [
        {"pmid": pid, "title": result[pid]["title"], "pubdate": result[pid]["pubdate"]}
        for pid in ids if pid in result
    ]


# ─────────────────────────────────────────────
# UniProt
# ─────────────────────────────────────────────
UNIPROT = "https://rest.uniprot.org/uniprotkb"


@mcp.tool()
def uniprot_search(query: str, max_results: int = 10) -> list[dict]:
    """Search UniProt for proteins by name, gene, function, or organism."""
    r = requests.get(f"{UNIPROT}/search", params={
        "query": query, "format": "json", "size": max_results,
        "fields": "accession,protein_name,gene_names,organism_name,length,reviewed"
    })
    return [
        {
            "accession": e["primaryAccession"],
            "name": e.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "N/A"),
            "gene": e.get("genes", [{}])[0].get("geneName", {}).get("value", "N/A") if e.get("genes") else "N/A",
            "organism": e.get("organism", {}).get("scientificName", "N/A"),
            "length": e.get("sequence", {}).get("length", "N/A"),
            "reviewed": e.get("entryType") == "UniProtKB reviewed (Swiss-Prot)",
        }
        for e in r.json().get("results", [])
    ]


@mcp.tool()
def uniprot_get(accession: str) -> dict:
    """Get full protein details from UniProt: function, location, organism, length."""
    e = requests.get(f"{UNIPROT}/{accession}", params={"format": "json"}).json()
    comments = {c["commentType"]: c for c in e.get("comments", []) if "commentType" in c}
    function_text = comments.get("FUNCTION", {}).get("texts", [{}])[0].get("value", "N/A")
    subcell = ", ".join(
        loc.get("location", {}).get("value", "")
        for loc in comments.get("SUBCELLULAR LOCATION", {}).get("subcellularLocations", [])
    ) or "N/A"
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
def uniprot_sequence(accession: str) -> str:
    """Get the FASTA sequence for a UniProt accession."""
    return requests.get(f"{UNIPROT}/{accession}", params={"format": "fasta"}).text.strip()


# ─────────────────────────────────────────────
# PDB
# ─────────────────────────────────────────────
PDB_DATA = "https://data.rcsb.org/rest/v1/core"
PDB_SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"


@mcp.tool()
def pdb_search(query: str, max_results: int = 10) -> list[dict]:
    """Search the PDB for protein structures by name, molecule, or keyword."""
    payload = {
        "query": {"type": "terminal", "service": "full_text", "parameters": {"value": query}},
        "return_type": "entry",
        "request_options": {"paginate": {"start": 0, "rows": max_results}}
    }
    r = requests.post(PDB_SEARCH, json=payload)
    if r.status_code != 200:
        return []
    results = []
    for hit in r.json().get("result_set", []):
        pdb_id = hit["identifier"]
        info = requests.get(f"{PDB_DATA}/entry/{pdb_id}").json()
        results.append({
            "pdb_id": pdb_id,
            "title": info.get("struct", {}).get("title", "N/A"),
            "method": info.get("exptl", [{}])[0].get("method", "N/A"),
            "resolution_angstrom": info.get("refine", [{}])[0].get("ls_d_res_high", "N/A"),
            "deposition_date": info.get("rcsb_accession_info", {}).get("deposit_date", "N/A"),
        })
    return results


@mcp.tool()
def pdb_get(pdb_id: str) -> dict:
    """Get detailed metadata for a PDB structure: method, resolution, chains, date."""
    pdb_id = pdb_id.upper()
    info = requests.get(f"{PDB_DATA}/entry/{pdb_id}").json()
    return {
        "pdb_id": pdb_id,
        "title": info.get("struct", {}).get("title", "N/A"),
        "method": info.get("exptl", [{}])[0].get("method", "N/A"),
        "resolution_angstrom": info.get("refine", [{}])[0].get("ls_d_res_high", "N/A"),
        "deposition_date": info.get("rcsb_accession_info", {}).get("deposit_date", "N/A"),
        "num_chains": len(info.get("rcsb_entry_container_identifiers", {}).get("asym_ids", []) or []),
        "rcsb_url": f"https://www.rcsb.org/structure/{pdb_id}",
    }


@mcp.tool()
def pdb_ligands(pdb_id: str) -> list[dict]:
    """List all small-molecule ligands bound in a PDB structure."""
    pdb_id = pdb_id.upper()
    info = requests.get(f"{PDB_DATA}/entry/{pdb_id}").json()
    nonpoly_ids = info.get("rcsb_entry_container_identifiers", {}).get("non_polymer_entity_ids", []) or []
    ligands = []
    for eid in nonpoly_ids:
        entity = requests.get(f"{PDB_DATA}/nonpolymer_entity/{pdb_id}/{eid}").json()
        chem = entity.get("pdbx_entity_nonpoly", {})
        ligands.append({
            "comp_id": chem.get("comp_id", "N/A"),
            "name": chem.get("name", "N/A"),
            "formula": entity.get("chem_comp", {}).get("formula", "N/A"),
        })
    return ligands


# ─────────────────────────────────────────────
# AlphaFold
# ─────────────────────────────────────────────
ALPHAFOLD = "https://alphafold.ebi.ac.uk/api"


@mcp.tool()
def alphafold_get(uniprot_accession: str) -> dict:
    """Get AlphaFold structure prediction for a UniProt accession: pLDDT score and download URLs."""
    r = requests.get(f"{ALPHAFOLD}/prediction/{uniprot_accession}")
    if r.status_code == 404 or not r.json():
        return {"error": f"No AlphaFold prediction found for {uniprot_accession}"}
    e = r.json()[0]
    return {
        "accession": e.get("uniprotAccession"),
        "gene": e.get("gene"),
        "protein_name": e.get("uniprotDescription"),
        "organism": e.get("organismScientificName"),
        "sequence_length": e.get("sequenceLength"),
        "model_version": e.get("latestVersion"),
        "mean_plddt": e.get("globalMetricValue"),
        "pdb_url": e.get("pdbUrl"),
        "cif_url": e.get("cifUrl"),
        "pae_image_url": e.get("paeImageUrl"),
    }


@mcp.tool()
def alphafold_search(gene_name: str, organism: str = "Homo sapiens") -> list[dict]:
    """Find AlphaFold predictions by gene name and organism."""
    r = requests.get("https://rest.uniprot.org/uniprotkb/search", params={
        "query": f"gene:{gene_name} AND organism_name:{organism} AND reviewed:true",
        "format": "json", "size": 5,
    })
    results = []
    for hit in r.json().get("results", []):
        accession = hit["primaryAccession"]
        af = requests.get(f"{ALPHAFOLD}/prediction/{accession}")
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


# ─────────────────────────────────────────────
# BLAST
# ─────────────────────────────────────────────
BLAST = "https://blast.ncbi.nlm.nih.gov/blast/Blast.cgi"


def _blast_submit(sequence: str, program: str, database: str) -> str:
    r = requests.put(BLAST, data={
        "CMD": "Put", "PROGRAM": program, "DATABASE": database,
        "QUERY": sequence, "FORMAT_TYPE": "JSON2", "HITLIST_SIZE": 10,
    })
    for line in r.text.splitlines():
        if line.strip().startswith("RID ="):
            return line.split("=")[1].strip()
    raise ValueError("Could not extract RID from BLAST response")


def _blast_poll(rid: str, timeout: int = 120) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(BLAST, params={"CMD": "Get", "RID": rid, "FORMAT_TYPE": "JSON2"})
        if "Status=WAITING" in r.text:
            time.sleep(10)
            continue
        if "Status=FAILED" in r.text:
            raise RuntimeError(f"BLAST job {rid} failed")
        if "Status=UNKNOWN" in r.text:
            raise RuntimeError(f"BLAST job {rid} expired")
        return r.text
    raise TimeoutError(f"BLAST job {rid} timed out after {timeout}s")


def _blast_parse(raw: str, max_hits: int) -> list[dict]:
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not match:
        return [{"error": "Could not parse BLAST response"}]
    try:
        hits = json.loads(match.group())["BlastOutput2"][0]["report"]["results"]["search"]["hits"]
    except (KeyError, IndexError):
        return [{"error": "No hits found"}]
    results = []
    for hit in hits[:max_hits]:
        desc = hit["description"][0]
        hsp = hit["hsps"][0]
        results.append({
            "title": desc.get("title", "N/A"),
            "accession": desc.get("accession", "N/A"),
            "sciname": desc.get("sciname", "N/A"),
            "identity_pct": round(hsp["identity"] / hsp["align_len"] * 100, 1),
            "evalue": hsp["evalue"],
            "bit_score": hsp["bit_score"],
        })
    return results


@mcp.tool()
def blast_protein(sequence: str, database: str = "nr", max_hits: int = 10) -> list[dict]:
    """Run BLASTp (protein vs protein) on NCBI. Takes 30-60s. database: nr, swissprot, pdb."""
    return _blast_parse(_blast_poll(_blast_submit(sequence, "blastp", database)), max_hits)


@mcp.tool()
def blast_nucleotide(sequence: str, database: str = "nt", max_hits: int = 10) -> list[dict]:
    """Run BLASTn (nucleotide vs nucleotide) on NCBI. Takes 30-60s. database: nt, refseq_rna."""
    return _blast_parse(_blast_poll(_blast_submit(sequence, "blastn", database)), max_hits)


@mcp.tool()
def blast_translated(sequence: str, database: str = "nr", max_hits: int = 10) -> list[dict]:
    """Run BLASTx (translated nucleotide vs protein) on NCBI. Takes 30-60s."""
    return _blast_parse(_blast_poll(_blast_submit(sequence, "blastx", database)), max_hits)


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print(f"Starting Lagomics MCP server on port {port}")
    mcp.run(transport="sse")
