from __future__ import annotations

import contextlib

from fastapi import FastAPI

from .mcp_server import mcp


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        yield


app = FastAPI(title="holded-mcp", lifespan=lifespan, redirect_slashes=False)


@app.get("/health")
async def health():
    return {"status": "ok"}

_mcp_http_app = mcp.streamable_http_app()
app.router.routes.extend(_mcp_http_app.routes)
