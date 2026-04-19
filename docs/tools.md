# Tools Reference

All 15 tools exposed by the Lagomics MCP server.

---

## PubMed

### `pubmed_search`
Search PubMed articles by any query term.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | string | required | PubMed search query |
| `max_results` | int | 10 | Number of results to return |

Returns: list of `{pmid, title, authors, journal, pubdate}`

---

### `pubmed_abstract`
Fetch the full abstract for an article.

| Parameter | Type | Description |
|---|---|---|
| `pmid` | string | PubMed article ID |

Returns: abstract text

---

### `pubmed_related`
Find articles similar to a given PMID, ranked by similarity.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `pmid` | string | required | Source article |
| `max_results` | int | 5 | Number of related articles |

---

## UniProt

### `uniprot_search`
Search UniProt by protein name, gene, function, or organism.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | string | required | Search query |
| `max_results` | int | 10 | Number of results |

Returns: list of `{accession, name, gene, organism, length, reviewed}`

---

### `uniprot_get`
Get full protein details by accession number.

| Parameter | Type | Description |
|---|---|---|
| `accession` | string | UniProt accession (e.g. `P04637`) |

Returns: `{accession, name, gene, organism, length, function, subcellular_location, reviewed}`

---

### `uniprot_sequence`
Get the FASTA sequence for a UniProt accession.

| Parameter | Type | Description |
|---|---|---|
| `accession` | string | UniProt accession |

Returns: FASTA string

---

## PDB

### `pdb_search`
Search the Protein Data Bank by molecule name or keyword.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | string | required | Search query |
| `max_results` | int | 10 | Number of results |

Returns: list of `{pdb_id, title, method, resolution_angstrom, deposition_date}`

---

### `pdb_get`
Get detailed metadata for a PDB structure.

| Parameter | Type | Description |
|---|---|---|
| `pdb_id` | string | PDB ID (e.g. `1TUP`) |

Returns: `{pdb_id, title, method, resolution_angstrom, num_chains, rcsb_url}`

---

### `pdb_ligands`
List all small-molecule ligands bound in a structure.

| Parameter | Type | Description |
|---|---|---|
| `pdb_id` | string | PDB ID |

Returns: list of `{comp_id, name, formula}`

---

## AlphaFold

### `alphafold_get`
Get predicted structure metadata for a UniProt accession.

| Parameter | Type | Description |
|---|---|---|
| `uniprot_accession` | string | UniProt accession (e.g. `P04637`) |

Returns: `{accession, gene, protein_name, organism, sequence_length, model_version, mean_plddt, pdb_url, cif_url}`

`mean_plddt` is the per-residue confidence score averaged across the sequence (0–100). Above 70 is generally reliable.

---

### `alphafold_search`
Find AlphaFold predictions by gene name and organism.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `gene_name` | string | required | Gene symbol (e.g. `TP53`) |
| `organism` | string | `Homo sapiens` | Organism name |

---

## BLAST

All BLAST tools submit a job to NCBI and poll for results. **Expect 30–60 seconds.**

### `blast_protein`
BLASTp — protein sequence vs protein database.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `sequence` | string | required | Amino acid sequence |
| `database` | string | `nr` | `nr`, `swissprot`, or `pdb` |
| `max_hits` | int | 10 | Number of hits to return |

Returns: list of `{title, accession, sciname, identity_pct, evalue, bit_score}`

---

### `blast_nucleotide`
BLASTn — nucleotide sequence vs nucleotide database.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `sequence` | string | required | Nucleotide sequence |
| `database` | string | `nt` | `nt` or `refseq_rna` |
| `max_hits` | int | 10 | Number of hits |

---

### `blast_translated`
BLASTx — translated nucleotide vs protein database. Useful when you have a DNA sequence and want to identify the protein it encodes.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `sequence` | string | required | Nucleotide sequence |
| `database` | string | `nr` | Protein database |
| `max_hits` | int | 10 | Number of hits |
