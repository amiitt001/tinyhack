class ConfigurationError(RuntimeError):
    """Raised when a required integration configuration is missing."""


class IntegrationError(RuntimeError):
    """Raised when an external integration fails safely."""


# ---------------------------------------------------------------------------
# TinyFish-specific exception hierarchy
# ---------------------------------------------------------------------------


class TinyFishError(IntegrationError):
    """Base class for all TinyFish adapter errors."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str | None = None,
        provider_run_id: str | None = None,
        duration_ms: int | None = None,
        started_at=None,
    ) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.provider_run_id = provider_run_id
        self.duration_ms = duration_ms
        self.started_at = started_at


class TinyFishAuthenticationError(TinyFishError):
    """API key is invalid, revoked, or missing (HTTP 401)."""


class TinyFishPaymentError(TinyFishError):
    """Account balance exhausted (HTTP 402)."""


class TinyFishRateLimitError(TinyFishError):
    """Too many requests — caller should back off (HTTP 429)."""


class TinyFishTimeoutError(TinyFishError):
    """Request did not complete within the configured timeout."""


class TinyFishConnectionError(TinyFishError):
    """Network-level failure (DNS, TCP, TLS)."""


class TinyFishInvalidResponseError(TinyFishError):
    """The provider returned a response that cannot be parsed or trusted."""


class TinyFishProviderError(TinyFishError):
    """Server-side error from TinyFish (5xx), may be transient."""
