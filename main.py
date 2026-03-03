import asyncio
import sys
import os
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from mcp_client import MCPClient
from core.claude import Claude
from core.local_llm import LocalLLM

from core.cli_chat import CliChat
from core.cli import CliApp

load_dotenv()

# Check if using local LLM
use_local_llm = os.getenv("USE_LOCAL_LLM", "0") == "1"

if use_local_llm:
    # Local LLM Config
    local_model = os.getenv("LOCAL_LLM_MODEL", "llama3")
    local_base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:12434/v1")
    local_api_key = os.getenv("LOCAL_LLM_API_KEY", "not-needed")
    
    assert local_model, "Error: LOCAL_LLM_MODEL cannot be empty. Update .env"
    assert local_base_url, "Error: LOCAL_LLM_BASE_URL cannot be empty. Update .env"
    
    print(f"Using Local LLM: {local_model} at {local_base_url}")
else:
    # Anthropic Config
    claude_model = os.getenv("CLAUDE_MODEL", "")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")

    assert claude_model, "Error: CLAUDE_MODEL cannot be empty. Update .env"
    assert anthropic_api_key, (
        "Error: ANTHROPIC_API_KEY cannot be empty. Update .env"
    )
    
    print(f"Using Anthropic Claude: {claude_model}")


async def main():
    # Create the appropriate LLM service based on configuration
    if use_local_llm:
        llm_service = LocalLLM(
            model=local_model,
            base_url=local_base_url,
            api_key=local_api_key,
        )
    else:
        llm_service = Claude(model=claude_model)

    server_scripts = sys.argv[1:]
    clients = {}

    command, args = (
        ("uv", ["run", "mcp_server.py"])
        if os.getenv("USE_UV", "0") == "1"
        else ("python", ["mcp_server.py"])
    )

    async with AsyncExitStack() as stack:
        doc_client = await stack.enter_async_context(
            MCPClient(command=command, args=args)
        )
        clients["doc_client"] = doc_client

        for i, server_script in enumerate(server_scripts):
            client_id = f"client_{i}_{server_script}"
            client = await stack.enter_async_context(
                MCPClient(command="uv", args=["run", server_script])
            )
            clients[client_id] = client

        chat = CliChat(
            doc_client=doc_client,
            clients=clients,
            claude_service=llm_service,  # Now uses either Claude or LocalLLM
        )

        cli = CliApp(chat)
        await cli.initialize()
        await cli.run()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
