"""
Custom exceptions for EIA API v2 client.
"""


class EIAError(Exception):
    """Base exception for all EIA API errors."""

    pass


class EIAAPIError(EIAError):
    """Exception raised when the EIA API returns an error response."""

    def __init__(self, message: str, code: int | None = None):
        self.message = message
        self.code = code
        super().__init__(f"EIA API Error (code {code}): {message}" if code else message)


class EIAValidationError(EIAError):
    """Exception raised when request validation fails."""

    pass
