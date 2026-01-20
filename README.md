# holded-mcp

Python MCP server (mcp SDK + FastMCP) on **FastAPI** to manage Holded **invoices (invoicing)**.

## Requirements

- Python 3.10+
- `HOLDED_API_KEY` environment variable

## Run locally

```bash
uv sync
export HOLDED_API_KEY="your_api_key"
uv run uvicorn holded_mcp.app:app --host 0.0.0.0 --port 8000
```

MCP endpoint:

- `http://localhost:8000/mcp`

## CLI (no MCP)

This repo also ships a CLI to call the same Holded endpoints.

```bash
export HOLDED_API_KEY="your_api_key"
holded-cli list --limit 5
```

If you did not install it globally yet, prefix with `uv run` from the repo:

```bash
uv sync
export HOLDED_API_KEY="your_api_key"
uv run holded-cli list --limit 5
```

### Global install (editable)

To use `holded-cli` from any folder and keep it updated as you edit the repo:

```bash
uv tool install -e .
uv tool update-shell
```

Or run the helper:

```bash
scripts/install-cli.sh
```

Examples (global install):

```bash
holded-cli get <document_id>
holded-cli create --payload @invoice.json
holded-cli update <document_id> --payload @invoice.json
holded-cli approve <document_id>
holded-cli delete <document_id>
holded-cli pay <document_id> --date 1700000000 --amount 100.0
holded-cli send <document_id> --emails "a@b.com,c@d.com"
holded-cli pdf <document_id>
```

## Use from Codex via STDIO (recommended)

1) In the repo:

```bash
uv sync
export HOLDED_API_KEY="your_api_key"
```

2) In `~/.codex/config.toml`:

```toml
[mcp_servers.holded]
command = "uv"
args = ["run", "--quiet", "python", "server.py"]
cwd = "/Users/antonio/Projects/antoniolg/holded-mcp"
env_vars = ["HOLDED_API_KEY"]
```

## Environment variables

- `HOLDED_API_KEY` (required)
- `HOLDED_BASE_URL` (optional, defaults to `https://api.holded.com/api/invoicing/v1`)
- `HOLDED_TIMEOUT_SECONDS` (optional, defaults to `20`)
