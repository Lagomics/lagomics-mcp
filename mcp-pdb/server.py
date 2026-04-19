import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("pdb")
DATA = "https://data.rcsb.org/rest/v1/core"
SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"


@mcp.tool()
def search_structures(query: str, max_results: int = 10) -> list[dict]:
    """Search the PDB for protein structures by name, molecule, or keyword."""
    payload = {
        "query": {
            "type": "terminal",
            "service": "full_text",
            "parameters": {"value": query}
        },
        "return_type": "entry",
        "request_options": {"paginate": {"start": 0, "rows": max_results}}
    }
    r = requests.post(SEARCH, json=payload)
    if r.status_code != 200:
        return []

    ids = [hit["identifier"] for hit in r.json().get("result_set", [])]
    results = []
    for pdb_id in ids:
        info = requests.get(f"{DATA}/entry/{pdb_id}").json()
        struct = info.get("struct", {})
        exp = info.get("exptl", [{}])[0]
        refine = info.get("refine", [{}])[0]
        results.append({
            "pdb_id": pdb_id,
            "title": struct.get("title", "N/A"),
            "method": exp.get("method", "N/A"),
            "resolution_angstrom": refine.get("ls_d_res_high", "N/A"),
            "deposition_date": info.get("rcsb_accession_info", {}).get("deposit_date", "N/A"),
        })
    return results


@mcp.tool()
def get_structure(pdb_id: str) -> dict:
    """Get detailed metadata for a PDB structure: authors, organism, ligands, chains."""
    pdb_id = pdb_id.upper()
    info = requests.get(f"{DATA}/entry/{pdb_id}").json()

    struct = info.get("struct", {})
    exp = info.get("exptl", [{}])[0]
    refine = info.get("refine", [{}])[0]
    entity_ids = [
        e["entity_id"]
        for e in info.get("rcsb_entry_container_identifiers", {}).get("entity_ids", []) or []
    ]

    return {
        "pdb_id": pdb_id,
        "title": struct.get("title", "N/A"),
        "method": exp.get("method", "N/A"),
        "resolution_angstrom": refine.get("ls_d_res_high", "N/A"),
        "deposition_date": info.get("rcsb_accession_info", {}).get("deposit_date", "N/A"),
        "release_date": info.get("rcsb_accession_info", {}).get("initial_release_date", "N/A"),
        "num_chains": len(info.get("rcsb_entry_container_identifiers", {}).get("asym_ids", []) or []),
        "entity_count": len(entity_ids),
        "rcsb_url": f"https://www.rcsb.org/structure/{pdb_id}",
    }


@mcp.tool()
def get_ligands(pdb_id: str) -> list[dict]:
    """List all small-molecule ligands bound in a PDB structure."""
    pdb_id = pdb_id.upper()
    info = requests.get(f"{DATA}/entry/{pdb_id}").json()
    nonpoly_ids = info.get("rcsb_entry_container_identifiers", {}).get("non_polymer_entity_ids", []) or []

    ligands = []
    for eid in nonpoly_ids:
        entity = requests.get(f"{DATA}/nonpolymer_entity/{pdb_id}/{eid}").json()
        chem = entity.get("pdbx_entity_nonpoly", {})
        ligands.append({
            "comp_id": chem.get("comp_id", "N/A"),
            "name": chem.get("name", "N/A"),
            "formula": entity.get("chem_comp", {}).get("formula", "N/A"),
        })
    return ligands


mcp.run()
