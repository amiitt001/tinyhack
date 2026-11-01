"""TinyFish adapter — hardened, typed, and exception-classified.

Design decisions
----------------
* ``base_url`` is intentionally left as ``None`` so the SDK uses the Search
  product hostname. The installed SDK source confirms that an explicit
  ``base_url`` instead routes Search to ``/v1/search`` on that base URL. This
  adapter ignores ``TINYFISH_BASE_URL`` to retain product-host routing.

* The adapter wraps SDK exceptions into the SkillSphere hierarchy so the
  rest of the codebase never imports from ``tinyfish._utils.exceptions``.

* Retries are not added on top of the SDK's built-in retry logic (``max_retries=2``
  with 0.5 s multiplier and 8 s cap).  Layering additional retries would
  multiply wait times and duplicate persisted results.  The adapter signals
  retryability via ``is_retryable`` on ``TinyFishError`` subclasses.

* Credentials are never logged.  ``repr(client)`` masks the key (SDK behaviour).

Verified API contract (tinyfish==0.11.0)
-----------------------------------------
* Search base URL : ``https://api.search.tinyfish.ai/`` (product host)
* HTTP method     : GET
* Authentication  : ``X-API-Key`` request header (set by SDK)
* Parameters      : query, location, language, include_domains, exclude_domains,
                    page (0–10), after_date, before_date, recency_minutes,
                    domain_type (web|news|research_paper)
* Response model  : ``SearchQueryResponse(query, results, total_results, page)``
* Result fields   : position, site_name, snippet, title, url, date?, publisher?
* Default timeout : 600 s (SDK-level)  — adapter enforces 120 s max
* SDK retries     : max_retries=2 (back-off details depend on the pinned SDK)
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import NamedTuple

from pydantic import ValidationError

from app.core.config import Settings
from app.core.exceptions import (
    ConfigurationError,
    TinyFishAuthenticationError,
    TinyFishConnectionError,
    TinyFishInvalidResponseError,
    TinyFishPaymentError,
    TinyFishProviderError,
    TinyFishRateLimitError,
    TinyFishTimeoutError,
)

logger = logging.getLogger(__name__)

# Adapter-level timeout cap.  The SDK default is 600 s; we cap at 120 s so
# that a single discovery request cannot hold a FastAPI worker indefinitely.
_ADAPTER_TIMEOUT_SECONDS: float = 120.0

# The SDK performs 2 built-in retries.  We document this and do not add more.
_SDK_MAX_RETRIES: int = 2
_PROVIDER_CONCURRENCY = threading.BoundedSemaphore(4)


@dataclass(frozen=True)
class SearchResultItem:
    """Typed, sanitised search result from TinyFish."""

    position: int
    title: str
    url: str
    site_name: str
    snippet: str
    date: str | None
    publisher: str | None
    discovered_at: datetime


class SearchResponse(NamedTuple):
    """Typed adapter response — wraps the raw SDK response cleanly."""

    query: str
    results: list[SearchResultItem]
    total_results: int
    page: int


class TinyFishAdapter:
    """Thin, hardened wrapper around the TinyFish Python SDK.

    This adapter:
    - Validates configuration at construction time.
    - Passes ``base_url=None`` to ensure the SDK uses correct product hosts.
    - Maps all SDK exceptions to the SkillSphere TinyFish exception hierarchy.
    - Never logs or exposes the API key.
    - Returns typed result objects, not raw SDK models.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.tinyfish_api_key:
            raise ConfigurationError("TINYFISH_API_KEY is not configured")

        self._api_key = settings.tinyfish_api_key

        # Document and warn if TINYFISH_BASE_URL is set — it routes search
        # through the agent host (/v1/search) instead of the correct product
        # host (https://api.search.tinyfish.ai/).
        if settings.tinyfish_base_url:
            logger.warning(
                "TINYFISH_BASE_URL is set but ignored; the TinyFish SDK product "
                "default is used for Search."
            )

    def search(
        self,
        query: str,
        *,
        location: str | None = None,
        include_domains: str | None = None,
        page: int = 0,
    ) -> SearchResponse:
        """Execute a TinyFish web search and return typed results.

        Args:
            query: Non-empty search query string.
            location: Optional location filter (e.g., "India").
            include_domains: Optional comma-separated domain allow-list.
            page: Result page (0–10, SDK-validated).

        Returns:
            ``SearchResponse`` with typed results.

        Raises:
            TinyFishAuthenticationError: API key rejected (HTTP 401).
            TinyFishPaymentError: Account balance exhausted (HTTP 402).
            TinyFishRateLimitError: Too many requests (HTTP 429).
            TinyFishTimeoutError: Request timed out.
            TinyFishConnectionError: Network failure.
            TinyFishInvalidResponseError: Response cannot be parsed.
            TinyFishProviderError: Server-side error (5xx).
        """
        # Import at call-site to isolate SDK dependency.
        from tinyfish import TinyFish
        from tinyfish._utils.exceptions import (
            APIConnectionError,
            APIStatusError,
            APITimeoutError,
            AuthenticationError,
            InternalServerError,
            PaymentRequiredError,
            RateLimitError,
        )

        # base_url=None — use SDK default product hosts (correct routing).
        client = TinyFish(
            api_key=self._api_key,
            base_url=None,
            timeout=_ADAPTER_TIMEOUT_SECONDS,
            max_retries=_SDK_MAX_RETRIES,
        )

        started = time.monotonic()
        try:
            with _PROVIDER_CONCURRENCY:
                response = client.search.query(
                    query,
                    location=location,
                    language="en",
                    include_domains=include_domains,
                    page=page,
                )
        except AuthenticationError as exc:
            raise TinyFishAuthenticationError(
                "TinyFish API key rejected", error_code="authentication_failed"
            ) from exc
        except PaymentRequiredError as exc:
            raise TinyFishPaymentError(
                "TinyFish account balance exhausted", error_code="payment_required"
            ) from exc
        except RateLimitError as exc:
            raise TinyFishRateLimitError(
                "TinyFish rate limit exceeded", error_code="rate_limited"
            ) from exc
        except APITimeoutError as exc:
            raise TinyFishTimeoutError("TinyFish request timed out", error_code="timeout") from exc
        except APIConnectionError as exc:
            raise TinyFishConnectionError(
                "TinyFish connection failed", error_code="connection_error"
            ) from exc
        except InternalServerError as exc:
            raise TinyFishProviderError(
                f"TinyFish server error (HTTP {exc.status_code})",
                error_code="provider_error",
            ) from exc
        except APIStatusError as exc:
            raise TinyFishProviderError(
                f"TinyFish API error (HTTP {exc.status_code})",
                error_code="api_error",
            ) from exc
        except ValidationError as exc:
            raise TinyFishInvalidResponseError(
                "TinyFish response failed schema validation", error_code="invalid_response"
            ) from exc
        except ValueError as exc:
            # SDK raises ValueError for invalid query params (empty query, etc.)
            raise TinyFishInvalidResponseError(
                f"TinyFish SDK parameter error: {exc}", error_code="invalid_params"
            ) from exc
        except Exception as exc:
            # Keep unexpected SDK/transport errors behind the stable integration boundary.
            raise TinyFishProviderError(
                "TinyFish search failed", error_code="unexpected_provider_error"
            ) from exc

        now = datetime.now(UTC)
        try:
            results = [
                SearchResultItem(
                    position=r.position,
                    title=r.title,
                    url=r.url,
                    site_name=r.site_name,
                    snippet=r.snippet,
                    date=r.date,
                    publisher=r.publisher,
                    discovered_at=now,
                )
                for r in response.results
            ]
            query_result = response.query
            total_results = response.total_results
            result_page = response.page
        except (AttributeError, TypeError, ValueError) as exc:
            raise TinyFishInvalidResponseError(
                "TinyFish response is missing required search fields",
                error_code="invalid_response",
            ) from exc

        logger.info(
            "TinyFish search succeeded query_length=%d duration_ms=%.1f "
            "total_results=%d page=%d items=%d",
            len(query),
            (time.monotonic() - started) * 1000,
            total_results,
            result_page,
            len(results),
        )

        return SearchResponse(
            query=query_result,
            results=results,
            total_results=total_results,
            page=result_page,
        )
