"""TinyFish 0.11.0 Search only; no browser agent, tool execution, or arbitrary base URL."""

import asyncio
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

from pydantic import ValidationError
from tinyfish import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AsyncTinyFish,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
    RequestTimeoutError,
)
from tinyfish.search.types import SearchQueryResponse

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, IntegrationError


class TinyFishProviderError(IntegrationError):
    code = "provider_error"
    retryable = False

    def __init__(self, *, attempts: int = 0, status: int | None = None, retry_after: float = 0):
        super().__init__(self.code)
        self.attempts = attempts
        self.status = status
        self.retry_after = retry_after


class TinyFishAuthenticationError(TinyFishProviderError):
    code = "provider_authentication"


class TinyFishRateLimitError(TinyFishProviderError):
    code = "provider_rate_limit"
    retryable = True


class TinyFishTimeoutError(TinyFishProviderError):
    code = "provider_timeout"
    retryable = True


class TinyFishConnectionError(TinyFishProviderError):
    code = "provider_connection"
    retryable = True


class TinyFishInvalidResponseError(TinyFishProviderError):
    code = "provider_invalid_response"


class TinyFishTransientError(TinyFishProviderError):
    code = "provider_unavailable"
    retryable = True


@dataclass(frozen=True)
class SourceRecord:
    title: str
    url: str
    source: str
    discovered_at: datetime
    verified_at: datetime | None = None
    verification_status: str = "unverified"


def retry_delay(value: str | None) -> float:
    if not value:
        return 0
    try:
        seconds = float(value)
    except ValueError:
        try:
            seconds = (parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds()
        except (ValueError, TypeError, OverflowError):
            return 0
    return max(0, seconds) if seconds < float("inf") else 0


class TinyFishAdapter:
    def __init__(
        self,
        settings: Settings,
        *,
        client_factory: Callable = AsyncTinyFish,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not settings.tinyfish_api_key or not settings.tinyfish_api_key.strip():
            raise ConfigurationError("TINYFISH_API_KEY is not configured")
        # SDK explicit base_url rewrites Search to /v1/search. Never reinterpret a legacy value.
        if settings.tinyfish_base_url and settings.tinyfish_base_url.strip():
            raise ConfigurationError(
                "Leave TINYFISH_BASE_URL empty: SDK Search uses its verified product host"
            )
        self.settings = settings
        self.client_factory = client_factory
        self.sleep = sleep
        self.attempt_count = 0

    def search(
        self,
        query: str,
        *,
        location: str | None = None,
        domains: tuple[str, ...] = ("canonical.com",),
        page: int = 0,
        deadline: float | None = None,
    ) -> list[SourceRecord]:
        if domains != ("canonical.com",) or not 0 <= page <= 10:
            raise ConfigurationError("Unsupported search policy")
        deadline = deadline or time.monotonic() + self.settings.discovery_timeout_seconds
        # The SDK location parameter is a country code, not a city. City remains plain query text.
        terms = f"{query} {location}" if location else query
        for attempt in range(1, self.settings.tinyfish_max_attempts + 1):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TinyFishTimeoutError(attempts=attempt - 1)
            self.attempt_count += 1
            error: TinyFishProviderError
            try:
                response = asyncio.run(
                    asyncio.wait_for(
                        self._query(
                            terms,
                            domains,
                            page,
                            min(remaining, self.settings.tinyfish_timeout_seconds),
                        ),
                        timeout=min(remaining, self.settings.tinyfish_timeout_seconds),
                    )
                )
                checked = SearchQueryResponse.model_validate(response.model_dump())
                if len(checked.results) > 100 or checked.total_results < 0 or checked.page != page:
                    raise TinyFishInvalidResponseError(attempts=attempt)
                now = datetime.now(UTC)
                records = []
                for item in checked.results:
                    if (
                        not item.title.strip()
                        or len(item.title) > 1000
                        or len(item.url) > 2048
                        or len(item.snippet) > 20_000
                    ):
                        raise TinyFishInvalidResponseError(attempts=attempt)
                    records.append(SourceRecord(item.title, item.url, "tinyfish_search", now))
                return records
            except (AuthenticationError, PermissionDeniedError):
                error = TinyFishAuthenticationError(attempts=attempt)
            except RateLimitError as exc:
                error = TinyFishRateLimitError(
                    attempts=attempt,
                    status=429,
                    retry_after=retry_delay(
                        exc.response.headers.get("Retry-After")
                        if exc.response is not None
                        else None
                    ),
                )
            except (TimeoutError, APITimeoutError, RequestTimeoutError):
                error = TinyFishTimeoutError(attempts=attempt)
            except APIConnectionError:
                error = TinyFishConnectionError(attempts=attempt)
            except APIStatusError as exc:
                error = (
                    TinyFishTransientError if exc.status_code >= 500 else TinyFishProviderError
                )(
                    attempts=attempt,
                    status=exc.status_code,
                    retry_after=retry_delay(
                        exc.response.headers.get("Retry-After")
                        if exc.response is not None
                        else None
                    ),
                )
            except (ValidationError, ValueError, TypeError, AttributeError):
                error = TinyFishInvalidResponseError(attempts=attempt)
            except APIError:
                error = TinyFishProviderError(attempts=attempt)
            # Do not retain/chains SDK bodies, headers, exception text or request objects.
            if not error.retryable or attempt == self.settings.tinyfish_max_attempts:
                raise error from None
            wait = max(
                error.retry_after,
                self.settings.tinyfish_retry_base_seconds * 2 ** (attempt - 1)
                + random.uniform(0, 0.25),
            )
            if wait > min(10, deadline - time.monotonic()):
                raise error from None
            self.sleep(wait)
        raise TinyFishProviderError()  # unreachable, defensive for static type analysis

    async def _query(self, terms: str, domains: tuple[str, ...], page: int, timeout: float):
        async with self.client_factory(
            api_key=self.settings.tinyfish_api_key, base_url=None, timeout=timeout, max_retries=0
        ) as client:
            return await client.search.query(
                terms,
                include_domains=",".join(domains),
                language="en",
                domain_type="web",
                page=page,
            )
