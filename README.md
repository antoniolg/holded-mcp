# holded-mcp

Servidor MCP en Python (SDK `mcp` + `FastMCP`) montado en **FastAPI** para gestionar **facturas (invoicing)** de Holded.

## Requisitos

- Python 3.10+
- Variable de entorno `HOLDED_API_KEY`

## Ejecutar en local

```bash
uv sync
export HOLDED_API_KEY="tu_api_key"
uv run uvicorn holded_mcp.app:app --host 0.0.0.0 --port 8000
```

Luego el endpoint MCP queda en:

- `http://localhost:8000/mcp`

## Usarlo desde Codex vía STDIO (recomendado)

1) En el repo:

```bash
uv sync
export HOLDED_API_KEY="tu_api_key"
```

2) En `~/.codex/config.toml`:

```toml
[mcp_servers.holded]
command = "uv"
args = ["run", "--quiet", "python", "server.py"]
cwd = "/Users/antonio/Documents/Develop/mcp/holded-mcp"
env_vars = ["HOLDED_API_KEY"]
```

## Variables de entorno

- `HOLDED_API_KEY` (obligatoria)
- `HOLDED_BASE_URL` (opcional, por defecto `https://api.holded.com/api/invoicing/v1`)
- `HOLDED_TIMEOUT_SECONDS` (opcional, por defecto `20`)
