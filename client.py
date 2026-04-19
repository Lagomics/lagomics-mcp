"""
Lagomics MCP Demo Client
Connects to all Tier 1 biotech MCP servers simultaneously and lets Claude
reason across all of them in a single conversation.
"""
import asyncio
import json
from contextlib import AsyncExitStack

import anthropic
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

SERVERS = {
    "pubmed":    ["python", "mcp-pubmed/server.py"],
    "uniprot":   ["python", "mcp-uniprot/server.py"],
    "pdb":       ["python", "mcp-pdb/server.py"],
    "alphafold": ["python", "mcp-alphafold/server.py"],
}

QUESTION = (
    "Tell me everything about TP53: "
    "what the protein does, its AlphaFold confidence score, "
    "any PDB structures with bound ligands, "
    "and the 3 most recent PubMed papers about it."
)


def dump(label, obj):
    try:
        data = obj if isinstance(obj, (dict, list)) else [b.model_dump() for b in obj]
        print(f"\n{'='*60}\n{label}\n{'='*60}")
        print(json.dumps(data, indent=2, default=str))
    except Exception:
        print(f"\n{label}:", obj)


async def run():
    async with AsyncExitStack() as stack:
        sessions = {}
        all_tools = []

        # Connect to all servers, keeping context managers alive via the stack
        print("Connecting to MCP servers...")
        for name, cmd in SERVERS.items():
            params = StdioServerParameters(command=cmd[0], args=cmd[1:])
            read, write = await stack.enter_async_context(stdio_client(params))
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()

            result = await session.list_tools()
            tools = [
                {
                    "name": f"{name}__{t.name}",  # prefix so Claude knows which server
                    "description": f"[{name}] {t.description}",
                    "input_schema": t.inputSchema,
                }
                for t in result.tools
            ]
            sessions[name] = session
            all_tools.extend(tools)
            print(f"  ✓ {name}: {[t['name'].split('__')[1] for t in tools]}")

        dump("ALL TOOLS AVAILABLE TO CLAUDE", all_tools)
        print(f"\nUser: {QUESTION}\n")

        client = anthropic.Anthropic()
        messages = [{"role": "user", "content": QUESTION}]
        turn = 0

        while True:
            turn += 1
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2048,
                tools=all_tools,
                messages=messages,
            )

            dump(f"CLAUDE RESPONSE (turn {turn}) — stop_reason: {response.stop_reason}", response.content)

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        print(f"\n{'='*60}\nFINAL ANSWER\n{'='*60}\n{block.text}")
                break

            # Execute all tool calls, routing each to the right server
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                # Unpack the server prefix to route to the right session
                server_name, tool_name = block.name.split("__", 1)
                session = sessions[server_name]

                print(f"\n  [MCP:{server_name}] {tool_name}({block.input})")
                result = await session.call_tool(tool_name, block.input)
                raw = result.content[0].text
                print(f"  [MCP:{server_name}] → {raw[:120]}{'...' if len(raw) > 120 else ''}")

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": raw,
                })

            dump(f"TOOL RESULTS SENT BACK (turn {turn})", tool_results)
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})


asyncio.run(run())
