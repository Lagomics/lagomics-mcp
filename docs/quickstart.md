# Quickstart

## Claude Desktop

Add the hosted server to your Claude Desktop config file:

**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "lagomics": {
      "url": "https://lagomics-mcp.onrender.com/sse"
    }
  }
}
```

Restart Claude Desktop. You should see the Lagomics tools available in the tool panel.

---

## Cursor / VS Code

In your MCP settings, add:

```json
{
  "lagomics": {
    "url": "https://lagomics-mcp.onrender.com/sse"
  }
}
```

---

## Python client

```python
import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def run():
    async with sse_client("https://lagomics-mcp.onrender.com/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([t.name for t in tools.tools])

asyncio.run(run())
```

---

## Example queries

Once connected, try these in Claude:

- *"What does BRCA1 do and where is it located in the cell?"*
- *"Find the highest-resolution PDB structure of insulin and list its ligands."*
- *"Search for the last 5 papers on CAR-T cell exhaustion."*
- *"What is the AlphaFold confidence score for KRAS? Is the structure well-predicted?"*
- *"BLAST this sequence and tell me what protein it is: MTEYKLVVVGAGGVGKSALTIQLIQNHFV"*
