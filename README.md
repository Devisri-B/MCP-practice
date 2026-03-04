# MCP Chat

MCP Chat is a command-line interface application that enables interactive chat capabilities with AI models. The application supports both **Anthropic Claude API** and **local LLMs** (via Docker/Ollama). It includes document retrieval, command-based prompts, and extensible tool integrations via the MCP (Model Control Protocol) architecture.

## Prerequisites

- Python 3.9+
- **Option A:** Anthropic API Key (for Claude models)
- **Option B:** Docker Desktop with a local LLM (Ollama, LM Studio, etc.)

## Setup

### Step 1: Configure the environment variables

1. Create or edit the `.env` file in the project root:

#### For Anthropic Claude (Cloud):

```env
USE_LOCAL_LLM=0
CLAUDE_MODEL="claude-sonnet-4-5"
ANTHROPIC_API_KEY="your-anthropic-api-key-here"
USE_UV=1
```

#### For Local LLM (Docker/Ollama):

```env
USE_LOCAL_LLM=1
LOCAL_LLM_BASE_URL="http://localhost:11434/v1"
LOCAL_LLM_MODEL="qwen3:4B-UD-Q4_K_XL"
LOCAL_LLM_API_KEY="not-needed"
USE_UV=1
```

### Step 2: Set up Local LLM with Docker (Optional)

If you want to use a local model instead of Anthropic's API:

#### Using Ollama in Docker

1. Pull and run Ollama:

```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

2. Download a model (e.g., Qwen, Llama, Mistral):

```bash
docker exec -it ollama ollama pull qwen3:4b
```

3. List available models:

```bash
docker exec -it ollama ollama list
```

4. Update your `.env` with the model name and port:

```env
USE_LOCAL_LLM=1
LOCAL_LLM_BASE_URL="http://localhost:11434/v1"
LOCAL_LLM_MODEL="qwen3:4b"
```

#### Common Local LLM Ports

| Server | Default Port | Base URL |
|--------|--------------|----------|
| Ollama | 11434 | `http://localhost:11434/v1` |
| LM Studio | 1234 | `http://localhost:1234/v1` |
| Custom | Varies | `http://localhost:PORT/v1` |

### Step 3: Install dependencies

#### Option 1: Setup with uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

1. Install uv, if not already installed:

```bash
pip install uv
```

2. Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
uv pip install -e .
```

4. Run the project:

```bash
uv run main.py
```

#### Option 2: Setup without uv

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install anthropic openai python-dotenv prompt-toolkit "mcp[cli]==1.8.0"
```

3. Run the project:

```bash
python main.py
```

## Usage

### Basic Interaction

Simply type your message and press Enter to chat with the model.

### Document Retrieval

Use the @ symbol followed by a document ID to include document content in your query:

```
> Tell me about @deposition.md
```

### Commands

Use the / prefix to execute commands defined in the MCP server:

```
> /summarize deposition.md
```

Commands will auto-complete when you press Tab.

## Development

### Adding New Documents

Edit the `mcp_server.py` file to add new documents to the `docs` dictionary.

### Implementing MCP Features

To fully implement the MCP features:

1. Complete the TODOs in `mcp_server.py`
2. Implement the missing functionality in `mcp_client.py`

## Switching Between Models

To switch between Anthropic Claude and your local LLM, simply change the `USE_LOCAL_LLM` setting in your `.env` file:

| Setting | Model Used |
|---------|------------|
| `USE_LOCAL_LLM=0` | Anthropic Claude (requires API key) |
| `USE_LOCAL_LLM=1` | Local LLM via Docker/Ollama |

## Troubleshooting

### Local LLM Connection Issues

1. **Verify Docker is running:**
   ```bash
   docker ps
   ```

2. **Check if the model is loaded:**
   ```bash
   docker exec -it ollama ollama list
   ```

3. **Test the API endpoint:**
   ```bash
   curl http://localhost:11434/v1/models
   ```

4. **Check container logs:**
   ```bash
   docker logs ollama
   ```

### Common Errors

| Error | Solution |
|-------|----------|
| `Connection refused` | Ensure Docker container is running and port is correct |
| `Model not found` | Pull the model: `docker exec -it ollama ollama pull MODEL_NAME` |
| `401 Unauthorized` | Check your API key (for Anthropic) or set `LOCAL_LLM_API_KEY="not-needed"` |

### Linting and Typing Check

There are no lint or type checks implemented.
