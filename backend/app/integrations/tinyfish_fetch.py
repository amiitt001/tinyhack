"""Safe wrapper around TinyFish Fetch for known, allowlisted static detail URLs."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.core.exceptions import (
    ConfigurationError,
    TinyFishInvalidResponseError,
    TinyFishProviderError,
)
from app.integrations.url_safety import validate_url


@dataclass(frozen=True)
class FetchPage:
    url: str
    final_url: str | None
    title: str | None
    text: str | None
    latency_ms: float | None


class TinyFishFetchAdapter:
    """Fetch one already-discovered public URL; redirects are checked after response."""

    def __init__(self, settings: Settings) -> None:
        if not settings.tinyfish_api_key:
            raise ConfigurationError("TINYFISH_API_KEY is not configured")
        self._key = settings.tinyfish_api_key

    def fetch(self, url: str, *, allowed_domains: list[str]) -> FetchPage:
        if not validate_url(url, allowed_domains=allowed_domains).is_valid:
            raise TinyFishInvalidResponseError(
                "Fetch URL is outside the approved source policy", error_code="invalid_url"
            )
        from tinyfish import TinyFish

        try:
            response = TinyFish(
                api_key=self._key, base_url=None, timeout=120, max_retries=1
            ).fetch.get_contents(
                urls=[url], format="markdown", links=True, ttl=3600, per_url_timeout_ms=110000
            )
        except Exception as exc:
            raise TinyFishProviderError("TinyFish Fetch failed", error_code="fetch_failed") from exc
        if not response.results:
            code = response.errors[0].error if response.errors else "empty_response"
            raise TinyFishProviderError("TinyFish Fetch returned no page", error_code=code)
        page = response.results[0]
        if (
            page.final_url
            and not validate_url(page.final_url, allowed_domains=allowed_domains).is_valid
        ):
            raise TinyFishInvalidResponseError(
                "Fetch redirected outside the approved source policy",
                error_code="invalid_redirect_url",
            )
        if not isinstance(page.text, str):
            raise TinyFishInvalidResponseError(
                "TinyFish Fetch returned no text content", error_code="invalid_content"
            )
        return FetchPage(page.url, page.final_url, page.title, page.text[:200000], page.latency_ms)
