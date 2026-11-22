"""Application error type. Services raise AppError; main.py turns it into a JSON response."""


class AppError(Exception):
    def __init__(self, status_code: int, detail: str, field: str | None = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.field = field
