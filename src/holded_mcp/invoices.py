from __future__ import annotations

import datetime as dt
from typing import Any

from .holded_client import HoldedClient


def _filter_items_by_date(items: list[Any], date_from: str | None, date_to: str | None) -> list[Any]:
    if date_from is None and date_to is None:
        return items

    start = dt.date.fromisoformat(date_from) if date_from is not None else None
    end = dt.date.fromisoformat(date_to) if date_to is not None else None

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
    return filtered


async def list_invoices(
    client: HoldedClient,
    *,
    status: int | None = None,
    current: bool | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    updated_from: str | None = None,
    updated_to: str | None = None,
    sort: str | None = None,
    order: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for key, value in {
        "status": status,
        "current": current,
        "dateFrom": date_from,
        "dateTo": date_to,
        "updatedFrom": updated_from,
        "updatedTo": updated_to,
        "sort": sort,
        "order": order,
        "limit": limit,
        "offset": offset,
    }.items():
        if value is not None:
            params[key] = value

    items = await client.request("GET", "/documents/invoice", params=params)
    if isinstance(items, list):
        items = _filter_items_by_date(items, date_from, date_to)
    return {"items": items}


async def get_invoice(client: HoldedClient, document_id: str) -> dict[str, Any]:
    return await client.request("GET", f"/documents/invoice/{document_id}")


async def create_invoice(client: HoldedClient, payload: dict[str, Any]) -> dict[str, Any]:
    return await client.request("POST", "/documents/invoice", json_body=payload)


async def update_invoice(client: HoldedClient, document_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return await client.request("PUT", f"/documents/invoice/{document_id}", json_body=payload)


async def approve_invoice(client: HoldedClient, document_id: str) -> dict[str, Any]:
    return await client.request("POST", f"/doc/invoice/{document_id}/draftmode/approve")


async def delete_invoice(client: HoldedClient, document_id: str) -> dict[str, Any]:
    return await client.request("DELETE", f"/documents/invoice/{document_id}")


async def pay_invoice(
    client: HoldedClient,
    document_id: str,
    *,
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
    return await client.request("POST", f"/documents/invoice/{document_id}/pay", json_body=payload)


async def send_invoice(
    client: HoldedClient,
    document_id: str,
    *,
    emails: str,
    subject: str | None = None,
    message: str | None = None,
    mail_template_id: str | None = None,
    doc_ids: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"emails": emails}
    if subject is not None:
        payload["subject"] = subject
    if message is not None:
        payload["message"] = message
    if mail_template_id is not None:
        payload["mailTemplateId"] = mail_template_id
    if doc_ids is not None:
        payload["docIds"] = doc_ids
    return await client.request("POST", f"/documents/invoice/{document_id}/send", json_body=payload)


async def invoice_pdf(client: HoldedClient, document_id: str) -> dict[str, Any]:
    return await client.request("GET", f"/documents/invoice/{document_id}/pdf")
