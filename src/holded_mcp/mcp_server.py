from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from .config import Settings
from .holded_client import HoldedClient
from .invoices import (
    approve_invoice,
    create_invoice,
    delete_invoice,
    get_invoice,
    invoice_pdf,
    list_invoices,
    pay_invoice,
    send_invoice,
    update_invoice,
)


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
    return await list_invoices(
        _ctx_holded(ctx),
        status=status,
        current=current,
        date_from=dateFrom,
        date_to=dateTo,
        updated_from=updatedFrom,
        updated_to=updatedTo,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
    )


@mcp.tool(description="Obtiene una factura por id (GET /documents/invoice/{documentId}).")
async def holded_invoices_get(ctx: Context, documentId: str) -> dict[str, Any]:
    return await get_invoice(_ctx_holded(ctx), documentId)


@mcp.tool(
    description=(
        "Crea una factura (POST /documents/invoice). "
        "El payload se envía tal cual; usa los campos de Holded (contactId/contactName, date, items, etc.)."
    )
)
async def holded_invoices_create(ctx: Context, payload: dict[str, Any]) -> dict[str, Any]:
    return await create_invoice(_ctx_holded(ctx), payload)


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
    return await update_invoice(_ctx_holded(ctx), documentId, payload)


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
    return await approve_invoice(_ctx_holded(ctx), documentId)


@mcp.tool(description="Elimina una factura (DELETE /documents/invoice/{documentId}).")
async def holded_invoices_delete(ctx: Context, documentId: str) -> dict[str, Any]:
    return await delete_invoice(_ctx_holded(ctx), documentId)


@mcp.tool(description="Marca una factura como pagada (POST /documents/invoice/{documentId}/pay).")
async def holded_invoices_pay(
    ctx: Context,
    documentId: str,
    date: int,
    amount: float,
    treasury: str | None = None,
    desc: str | None = None,
) -> dict[str, Any]:
    return await pay_invoice(
        _ctx_holded(ctx),
        documentId,
        date=date,
        amount=amount,
        treasury=treasury,
        desc=desc,
    )


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
    return await send_invoice(
        _ctx_holded(ctx),
        documentId,
        emails=emails,
        subject=subject,
        message=message,
        mail_template_id=mailTemplateId,
        doc_ids=docIds,
    )


@mcp.tool(description="Obtiene el PDF (base64) de una factura (GET /documents/invoice/{documentId}/pdf).")
async def holded_invoices_pdf(ctx: Context, documentId: str) -> dict[str, Any]:
    return await invoice_pdf(_ctx_holded(ctx), documentId)
