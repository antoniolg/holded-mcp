from __future__ import annotations

import json
from typing import Any

import httpx

from .config import Settings
from .errors import HoldedAPIError


class HoldedClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            base_url=settings.holded_base_url.rstrip("/"),
            follow_redirects=True,
            timeout=httpx.Timeout(settings.holded_timeout_seconds),
            headers={
                "Content-Type": "application/json",
                "key": settings.holded_api_key,
            },
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
    ) -> Any:
        url = path if path.startswith("/") else f"/{path}"
        try:
            resp = await self._client.request(method, url, params=params, json=json_body)
        except httpx.RequestError as e:
            raise HoldedAPIError(message=f"Network error calling Holded: {e}") from e

        if resp.status_code >= 400:
            text = None
            try:
                text = resp.text
            except Exception:
                text = None
            raise HoldedAPIError(
                message=f"Holded API error ({resp.status_code}) calling {method.upper()} {url}",
                status_code=resp.status_code,
                response_text=text,
                method=method.upper(),
                url=str(resp.request.url),
            )

        # Holded API endpoints we use are expected to return JSON. If we receive HTML
        # (e.g. an app page, WAF page, or unexpected redirect target), fail with a
        # clear error instead of returning a string that breaks tool output validation.
        try:
            return resp.json()
        except Exception:
            content_type = resp.headers.get("content-type", "")
            raw = resp.text
            snippet = raw[:800]
            raise HoldedAPIError(
                message=(
                    "Holded returned a non-JSON response for an API request. "
                    "Check HOLDED_BASE_URL and HOLDED_API_KEY. "
                    f"(status={resp.status_code}, content-type={content_type})"
                ),
                status_code=resp.status_code,
                response_text=snippet,
                method=method.upper(),
                url=str(resp.request.url),
            )
