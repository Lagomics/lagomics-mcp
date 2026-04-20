import asyncio
import httpx
import nest_asyncio
import anthropic
import streamlit as st
from mcp import ClientSession
from mcp.client.sse import sse_client

nest_asyncio.apply()  # fix: Streamlit runs its own event loop

SERVER_URL = "https://lagomics-mcp.onrender.com/sse"
WARMUP_URL = "https://lagomics-mcp.onrender.com/"

EXAMPLES = [
    "Tell me everything about TP53 — function, AlphaFold confidence, PDB structures with ligands, and 3 recent papers.",
    "What does BRCA1 do and where is it located in the cell?",
    "Find the highest-resolution PDB structure of insulin and list its bound ligands.",
    "What is the AlphaFold confidence score for KRAS? Is the disordered region well-predicted?",
    "Search for the 5 most recent papers on CAR-T cell exhaustion.",
]

st.set_page_config(page_title="Lagomics MCP Demo", page_icon="🧬", layout="wide")
st.title("🧬 Lagomics MCP Demo")
st.caption("Live AI queries across PubMed · UniProt · PDB · AlphaFold · BLAST")

with st.sidebar:
    st.header("Setup")
    api_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
    st.caption("Your key is used only for this session and never stored.")
    st.divider()
    st.header("Example queries")
    for ex in EXAMPLES:
        if st.button(ex[:60] + "…", key=ex):
            st.session_state["question"] = ex

question = st.text_area(
    "Ask anything about a gene, protein, or disease",
    value=st.session_state.get("question", ""),
    height=100,
    placeholder="e.g. Tell me everything about TP53",
)


def warmup_server():
    """Ping the server to wake it from Render's free-tier sleep."""
    try:
        httpx.get(WARMUP_URL, timeout=30)
    except Exception:
        pass


async def run_query(question: str, api_key: str):
    async with sse_client(SERVER_URL, timeout=60) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            tools = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema,
                }
                for t in result.tools
            ]

            client = anthropic.Anthropic(api_key=api_key)
            messages = [{"role": "user", "content": question}]
            tool_log = []
            final_text = ""

            while True:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=2048,
                    tools=tools,
                    messages=messages,
                )

                if response.stop_reason == "end_turn":
                    for block in response.content:
                        if hasattr(block, "text"):
                            final_text = block.text
                    break

                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    result = await session.call_tool(block.name, block.input)
                    raw = result.content[0].text
                    tool_log.append((block.name, block.input, raw))
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": raw,
                    })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

            return final_text, tool_log


if st.button("Search", type="primary", disabled=not (api_key and question)):
    if not api_key:
        st.error("Enter your Anthropic API key in the sidebar.")
    elif not question:
        st.error("Enter a question.")
    else:
        try:
            with st.spinner("Waking up server (first request may take ~30s on free tier)..."):
                warmup_server()

            with st.spinner("Querying databases..."):
                loop = asyncio.get_event_loop()
                answer, tool_log = loop.run_until_complete(run_query(question, api_key))

            st.subheader("Answer")
            st.markdown(answer)

            if tool_log:
                with st.expander(f"Database calls ({len(tool_log)} tools called)"):
                    for name, inputs, output in tool_log:
                        st.markdown(f"**`{name}`** — `{inputs}`")
                        st.code(output[:500] + ("..." if len(output) > 500 else ""), language="json")

        except Exception as e:
            msg = str(e)
            if "TaskGroup" in msg or "ConnectionError" in msg or "ConnectError" in msg:
                st.error("Could not reach the MCP server. It may still be waking up — wait 15 seconds and try again.")
            else:
                st.error(f"Error: {msg}")

st.divider()
st.caption(
    "Powered by [Lagomics MCP](https://github.com/Lagomics/lagomics-mcp) · "
    "Data from NCBI, UniProt, RCSB PDB, EBI AlphaFold · "
    "No data is stored."
)
