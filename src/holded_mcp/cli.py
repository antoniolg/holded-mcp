from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any

from pydantic import ValidationError

from .config import Settings
from .errors import HoldedAPIError
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


def _load_json(value: str) -> Any:
    if value == "-":
        raw = sys.stdin.read()
    elif value.startswith("@"):
        with open(value[1:], "r", encoding="utf-8") as handle:
            raw = handle.read()
    else:
        raw = value
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON payload: {exc.msg}") from exc


def _add_current_flags(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--current", dest="current", action="store_true", help="Only current invoices")
    group.add_argument("--no-current", dest="current", action="store_false", help="Exclude current invoices")
    parser.set_defaults(current=None)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="holded-cli", description="Holded invoicing CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List invoices")
    list_parser.add_argument("--status", type=int, help="Invoice status")
    _add_current_flags(list_parser)
    list_parser.add_argument("--date-from", dest="date_from", help="Filter by date from (YYYY-MM-DD)")
    list_parser.add_argument("--date-to", dest="date_to", help="Filter by date to (YYYY-MM-DD)")
    list_parser.add_argument("--updated-from", dest="updated_from", help="Filter by updated from (YYYY-MM-DD)")
    list_parser.add_argument("--updated-to", dest="updated_to", help="Filter by updated to (YYYY-MM-DD)")
    list_parser.add_argument("--sort", help="Sort field")
    list_parser.add_argument("--order", help="Order direction")
    list_parser.add_argument("--limit", type=int, help="Limit results")
    list_parser.add_argument("--offset", type=int, help="Offset results")

    get_parser = subparsers.add_parser("get", help="Get invoice by id")
    get_parser.add_argument("document_id", help="Invoice document id")

    create_parser = subparsers.add_parser("create", help="Create invoice")
    create_parser.add_argument("--payload", required=True, help="JSON payload, @file, or '-' for stdin")

    update_parser = subparsers.add_parser("update", help="Update invoice")
    update_parser.add_argument("document_id", help="Invoice document id")
    update_parser.add_argument("--payload", required=True, help="JSON payload, @file, or '-' for stdin")

    approve_parser = subparsers.add_parser("approve", help="Approve invoice")
    approve_parser.add_argument("document_id", help="Invoice document id")

    delete_parser = subparsers.add_parser("delete", help="Delete invoice")
    delete_parser.add_argument("document_id", help="Invoice document id")

    pay_parser = subparsers.add_parser("pay", help="Mark invoice as paid")
    pay_parser.add_argument("document_id", help="Invoice document id")
    pay_parser.add_argument("--date", required=True, type=int, help="Unix timestamp (seconds)")
    pay_parser.add_argument("--amount", required=True, type=float, help="Amount paid")
    pay_parser.add_argument("--treasury", help="Treasury id")
    pay_parser.add_argument("--desc", help="Payment description")

    send_parser = subparsers.add_parser("send", help="Send invoice via email")
    send_parser.add_argument("document_id", help="Invoice document id")
    send_parser.add_argument("--emails", required=True, help="Comma-separated emails")
    send_parser.add_argument("--subject", help="Email subject")
    send_parser.add_argument("--message", help="Email message")
    send_parser.add_argument("--mail-template-id", dest="mail_template_id", help="Holded mail template id")
    send_parser.add_argument("--doc-ids", dest="doc_ids", help="Additional doc ids")

    pdf_parser = subparsers.add_parser("pdf", help="Get invoice PDF (base64)")
    pdf_parser.add_argument("document_id", help="Invoice document id")

    return parser


async def _run_command(args: argparse.Namespace) -> Any:
    settings = Settings()
    client = HoldedClient(settings)
    try:
        if args.command == "list":
            return await list_invoices(
                client,
                status=args.status,
                current=args.current,
                date_from=args.date_from,
                date_to=args.date_to,
                updated_from=args.updated_from,
                updated_to=args.updated_to,
                sort=args.sort,
                order=args.order,
                limit=args.limit,
                offset=args.offset,
            )
        if args.command == "get":
            return await get_invoice(client, args.document_id)
        if args.command == "create":
            payload = _load_json(args.payload)
            if not isinstance(payload, dict):
                raise ValueError("Payload must be a JSON object")
            return await create_invoice(client, payload)
        if args.command == "update":
            payload = _load_json(args.payload)
            if not isinstance(payload, dict):
                raise ValueError("Payload must be a JSON object")
            return await update_invoice(client, args.document_id, payload)
        if args.command == "approve":
            return await approve_invoice(client, args.document_id)
        if args.command == "delete":
            return await delete_invoice(client, args.document_id)
        if args.command == "pay":
            return await pay_invoice(
                client,
                args.document_id,
                date=args.date,
                amount=args.amount,
                treasury=args.treasury,
                desc=args.desc,
            )
        if args.command == "send":
            return await send_invoice(
                client,
                args.document_id,
                emails=args.emails,
                subject=args.subject,
                message=args.message,
                mail_template_id=args.mail_template_id,
                doc_ids=args.doc_ids,
            )
        if args.command == "pdf":
            return await invoice_pdf(client, args.document_id)
        raise ValueError(f"Unknown command: {args.command}")
    finally:
        await client.aclose()


def _print_error(error: Exception) -> None:
    if isinstance(error, HoldedAPIError):
        lines = [f"Holded API error: {error}"]
        if error.status_code is not None:
            lines.append(f"status: {error.status_code}")
        if error.method is not None and error.url is not None:
            lines.append(f"request: {error.method} {error.url}")
        if error.response_text:
            lines.append(f"response: {error.response_text}")
        print("\n".join(lines), file=sys.stderr)
        return
    print(str(error), file=sys.stderr)


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        result = asyncio.run(_run_command(args))
    except ValidationError as exc:
        _print_error(exc)
        sys.exit(2)
    except (HoldedAPIError, ValueError) as exc:
        _print_error(exc)
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
