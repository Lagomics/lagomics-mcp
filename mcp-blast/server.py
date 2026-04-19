import time
import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("blast")
BASE = "https://blast.ncbi.nlm.nih.gov/blast/Blast.cgi"


def _submit(sequence: str, program: str, database: str) -> str:
    """Submit a BLAST job and return the RID (request ID)."""
    r = requests.put(BASE, data={
        "CMD": "Put",
        "PROGRAM": program,
        "DATABASE": database,
        "QUERY": sequence,
        "FORMAT_TYPE": "JSON2",
        "HITLIST_SIZE": 10,
    })
    for line in r.text.splitlines():
        if line.strip().startswith("RID ="):
            return line.split("=")[1].strip()
    raise ValueError("Could not extract RID from BLAST submission response")


def _poll(rid: str, timeout: int = 120) -> str:
    """Poll until BLAST job is ready, return raw JSON result."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = requests.get(BASE, params={
            "CMD": "Get", "RID": rid, "FORMAT_TYPE": "JSON2"
        })
        if "Status=WAITING" in r.text:
            time.sleep(10)
            continue
        if "Status=FAILED" in r.text:
            raise RuntimeError(f"BLAST job {rid} failed")
        if "Status=UNKNOWN" in r.text:
            raise RuntimeError(f"BLAST job {rid} expired or unknown")
        return r.text  # ready
    raise TimeoutError(f"BLAST job {rid} timed out after {timeout}s")


def _parse_hits(raw: str, max_hits: int) -> list[dict]:
    """Extract top hits from BLAST JSON2 response."""
    import json, re
    # JSON2 format wraps the result — extract the JSON object
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if not match:
        return [{"error": "Could not parse BLAST response"}]

    data = json.loads(match.group())
    try:
        hits = data["BlastOutput2"][0]["report"]["results"]["search"]["hits"]
    except (KeyError, IndexError):
        return [{"error": "No hits found"}]

    results = []
    for hit in hits[:max_hits]:
        desc = hit["description"][0]
        hsp = hit["hsps"][0]
        results.append({
            "title": desc.get("title", "N/A"),
            "accession": desc.get("accession", "N/A"),
            "taxid": desc.get("taxid", "N/A"),
            "sciname": desc.get("sciname", "N/A"),
            "identity_pct": round(hsp["identity"] / hsp["align_len"] * 100, 1),
            "coverage_pct": round(hsp["align_len"] / hsp.get("query_len", hsp["align_len"]) * 100, 1),
            "evalue": hsp["evalue"],
            "bit_score": hsp["bit_score"],
        })
    return results


@mcp.tool()
def blast_protein(sequence: str, database: str = "nr", max_hits: int = 10) -> list[dict]:
    """
    Run BLASTp (protein vs protein) on NCBI. Takes ~30-60s.
    sequence: amino acid sequence (single-letter code)
    database: 'nr' (non-redundant), 'swissprot', 'pdb'
    """
    rid = _submit(sequence, "blastp", database)
    raw = _poll(rid)
    return _parse_hits(raw, max_hits)


@mcp.tool()
def blast_nucleotide(sequence: str, database: str = "nt", max_hits: int = 10) -> list[dict]:
    """
    Run BLASTn (nucleotide vs nucleotide) on NCBI. Takes ~30-60s.
    sequence: nucleotide sequence (ACGT)
    database: 'nt' (nucleotide), 'refseq_rna', 'refseq_genomic'
    """
    rid = _submit(sequence, "blastn", database)
    raw = _poll(rid)
    return _parse_hits(raw, max_hits)


@mcp.tool()
def blastx_sequence(sequence: str, database: str = "nr", max_hits: int = 10) -> list[dict]:
    """
    Run BLASTx (translated nucleotide vs protein) on NCBI. Takes ~30-60s.
    Useful when you have a DNA sequence and want to find the protein it encodes.
    """
    rid = _submit(sequence, "blastx", database)
    raw = _poll(rid)
    return _parse_hits(raw, max_hits)


mcp.run()
