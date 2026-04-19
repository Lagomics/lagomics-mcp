# Self-hosting

Run your own instance if you want full control or higher rate limits.

## Local (stdio)

Each server can be run locally over stdio for use with Claude Desktop:

```bash
git clone https://github.com/Lagomics/lagomics-mcp
cd lagomics-mcp
pip install -r requirements.txt
```

Claude Desktop config for local stdio:

```json
{
  "mcpServers": {
    "pubmed": {
      "command": "python",
      "args": ["/path/to/lagomics-mcp/mcp-pubmed/server.py"]
    },
    "uniprot": {
      "command": "python",
      "args": ["/path/to/lagomics-mcp/mcp-uniprot/server.py"]
    }
  }
}
```

## Remote (SSE) on Render

Deploy the combined server to Render in one click:

1. Fork the repo on GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your fork — Render auto-detects `render.yaml`
4. Deploy

Your server will be live at `https://<your-service>.onrender.com/sse`.

No environment variables required — all data sources are free public APIs.

## Remote (SSE) on Fly.io

```bash
fly launch --name lagomics-mcp
fly deploy
```

## Rate limits

The underlying APIs are free and public but have soft rate limits:

| API | Limit | Notes |
|---|---|---|
| NCBI (PubMed, BLAST) | 3 req/s unauthenticated, 10 req/s with API key | Set `NCBI_API_KEY` env var |
| UniProt | 200 req/s | No key needed |
| RCSB PDB | No hard limit | No key needed |
| AlphaFold EBI | No hard limit | No key needed |

For high-traffic deployments, register a free NCBI API key at [ncbi.nlm.nih.gov/account](https://www.ncbi.nlm.nih.gov/account/).
