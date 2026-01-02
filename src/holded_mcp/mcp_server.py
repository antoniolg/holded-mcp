from __future__ import annotations

import datetime as dt
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from .config import Settings
from .holded_client import HoldedClient


@dataclass(frozen=True)
class AppContext:
    settings: Settings
    holded: HoldedClient


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    settings = Settings()
    holded = HoldedClient(settings)
    try:
        yield AppContext(settings=settings, holded=holded)
    finally:
        await holded.aclose()


mcp = FastMCP(name="Holded Invoicing", lifespan=app_lifespan, stateless_http=True)


def _ctx_holded(ctx: Context) -> HoldedClient:
    return ctx.request_context.lifespan_context.holded


@mcp.tool(description="Lista facturas (type=invoice) con filtros opcionales.")
async def holded_invoices_list(
    ctx: Context,
    status: int | None = None,
    current: bool | None = None,
    dateFrom: str | None = None,
    dateTo: str | None = None,
    updatedFrom: str | None = None,
    updatedTo: str | None = None,
    sort: str | None = None,
    order: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> dict[str, Any]:
    """
    GET /documents/invoice
    - dateFrom/dateTo/updatedFrom/updatedTo: YYYY-MM-DD
    - status: según Holded (p.ej. 0 borrador, 1 pendiente, 2 aprobada)
    """
    params: dict[str, Any] = {}
    for key, value in {
        "status": status,
        "current": current,
        "dateFrom": dateFrom,
        "dateTo": dateTo,
        "updatedFrom": updatedFrom,
        "updatedTo": updatedTo,
        "sort": sort,
        "order": order,
        "limit": limit,
        "offset": offset,
    }.items():
        if value is not None:
            params[key] = value
    items = await _ctx_holded(ctx).request("GET", "/documents/invoice", params=params)

    # Holded's date filters may not be consistently applied by the API, so we
    # also filter client-side when the caller provides a date range.
    if (dateFrom is not None or dateTo is not None) and isinstance(items, list):
        start = dt.date.fromisoformat(dateFrom) if dateFrom is not None else None
        end = dt.date.fromisoformat(dateTo) if dateTo is not None else None

        filtered: list[Any] = []
        for it in items:
            if not isinstance(it, dict):
                continue
            ts = it.get("date")
            if not isinstance(ts, (int, float)):
                continue
            d = dt.datetime.utcfromtimestamp(ts).date()
            if start is not None and d < start:
                continue
            if end is not None and d > end:
                continue
            filtered.append(it)
        items = filtered

    return {"items": items}


@mcp.tool(description="Obtiene una factura por id (GET /documents/invoice/{documentId}).")
async def holded_invoices_get(ctx: Context, documentId: str) -> dict[str, Any]:
    return await _ctx_holded(ctx).request("GET", f"/documents/invoice/{documentId}")


@mcp.tool(
    description=(
        "Crea una factura (POST /documents/invoice). "
        "El payload se envía tal cual; usa los campos de Holded (contactId/contactName, date, items, etc.)."
    )
)
async def holded_invoices_create(ctx: Context, payload: dict[str, Any]) -> dict[str, Any]:
    return await _ctx_holded(ctx).request("POST", "/documents/invoice", json_body=payload)


@mcp.tool(
    description=(
        "Actualiza una factura (PUT /documents/invoice/{documentId}). "
        "El payload se envía tal cual; permite actualizar desc/notes/date/items/customFields, etc."
    )
)
async def holded_invoices_update(
    ctx: Context,
    documentId: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return await _ctx_holded(ctx).request("PUT", f"/documents/invoice/{documentId}", json_body=payload)


@mcp.tool(
    description=(
        "Aprueba/numera una factura. "
        "Equivale a la acción 'Aprobar/Emitir' del panel web y usa "
        "POST /doc/invoice/{documentId}/draftmode/approve."
    )
)
async def holded_invoices_approve(
    ctx: Context,
    documentId: str,
    info: str | None = None,
) -> dict[str, Any]:
    # El endpoint de aprobación de la app web no requiere body; solo POST.
    # Conservamos info por compatibilidad futura (no se envía).
    _ = info  # unused
    return await _ctx_holded(ctx).request("POST", f"/doc/invoice/{documentId}/draftmode/approve")


@mcp.tool(description="Elimina una factura (DELETE /documents/invoice/{documentId}).")
async def holded_invoices_delete(ctx: Context, documentId: str) -> dict[str, Any]:
    return await _ctx_holded(ctx).request("DELETE", f"/documents/invoice/{documentId}")


@mcp.tool(description="Marca una factura como pagada (POST /documents/invoice/{documentId}/pay).")
async def holded_invoices_pay(
    ctx: Context,
    documentId: str,
    date: int,
    amount: float,
    treasury: str | None = None,
    desc: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"date": date, "amount": amount}
    if treasury is not None:
        payload["treasury"] = treasury
    if desc is not None:
        payload["desc"] = desc
    return await _ctx_holded(ctx).request("POST", f"/documents/invoice/{documentId}/pay", json_body=payload)


@mcp.tool(description="Envía una factura por email (POST /documents/invoice/{documentId}/send).")
async def holded_invoices_send(
    ctx: Context,
    documentId: str,
    emails: str,
    subject: str | None = None,
    message: str | None = None,
    mailTemplateId: str | None = None,
    docIds: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"emails": emails}
    if subject is not None:
        payload["subject"] = subject
    if message is not None:
        payload["message"] = message
    if mailTemplateId is not None:
        payload["mailTemplateId"] = mailTemplateId
    if docIds is not None:
        payload["docIds"] = docIds
    return await _ctx_holded(ctx).request("POST", f"/documents/invoice/{documentId}/send", json_body=payload)


@mcp.tool(description="Obtiene el PDF (base64) de una factura (GET /documents/invoice/{documentId}/pdf).")
async def holded_invoices_pdf(ctx: Context, documentId: str) -> dict[str, Any]:
    return await _ctx_holded(ctx).request("GET", f"/documents/invoice/{documentId}/pdf")
