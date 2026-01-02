from __future__ import annotations


class HoldedAPIError(RuntimeError):
    def __init__(
        self,
        *,
        message: str,
        status_code: int | None = None,
        response_text: str | None = None,
        method: str | None = None,
        url: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
        self.method = method
        self.url = url

