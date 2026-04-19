# Lagomics MCP

MCP servers that give Claude and other AI assistants direct, live access to the databases biotech researchers use every day.

**Hosted server** — no install required:
```
https://lagomics-mcp.onrender.com/sse
```

**What's included:**

| Server | Databases | Tools |
|---|---|---|
| PubMed | NCBI Entrez | Search, abstracts, related articles |
| UniProt | Swiss-Prot / TrEMBL | Search, protein details, FASTA |
| PDB | RCSB | Search structures, metadata, ligands |
| AlphaFold | EBI AlphaFold DB | Get prediction, search by gene |
| BLAST | NCBI BLAST | BLASTp, BLASTn, BLASTx |

## Try it

Ask Claude:

> *"Tell me everything about TP53 — what the protein does, its AlphaFold confidence, PDB structures with bound ligands, and the 3 most recent papers about it."*

Claude will query PubMed, UniProt, PDB, and AlphaFold simultaneously and return a structured briefing from live data.

## Get started

→ [Quickstart](quickstart.md) — connect Claude Desktop in 2 minutes  
→ [Tools Reference](tools.md) — all 15 tools documented  
→ [Self-hosting](self-host.md) — run your own instance  
