Biotech still spends too much time stitching together public data by hand.

Search PubMed in one tab. Check UniProt in another. Open PDB. Look up AlphaFold. Copy accession numbers around. Repeat.

We wanted to make that workflow less painful.

So we open-sourced a lightweight set of MCP servers for biotech that lets Claude, Cursor, and other MCP-compatible clients directly query databases like:

- PubMed
- UniProt
- PDB
- AlphaFold DB

That means one prompt can pull live results across literature, protein function, structures, and predicted models — without the usual tab-switching and copy-paste.

For example, we asked:

*"Tell me everything about TP53 — what the protein does, its AlphaFold confidence, any PDB structures with bound ligands, and the 3 most recent PubMed papers about it."*

The AI queried multiple sources simultaneously and returned a structured briefing from live database results — protein function from UniProt, pLDDT score from AlphaFold, ligand-bound structures from PDB, and papers published this week from PubMed.

This does not replace scientific judgment. It does remove a lot of the manual glue work that slows people down.

That is the part we care about.

MCP is now a well-established open protocol with a growing ecosystem of servers across many domains. Biology deserves better versions of that interface layer — built around the databases researchers actually use every day. There are already public efforts in this space (BioMCP, MCPmed, and others), and we see this as part of that broader movement.

This is our early step in that direction.

Current sources: PubMed, UniProt, PDB, AlphaFold DB. We're exploring expanding to ChEMBL, OpenTargets, ClinicalTrials.gov, gnomAD, Ensembl, STRING, and Reactome next.

Code is open source. Drop a comment if you want the link.
