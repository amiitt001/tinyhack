from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from tinyfish import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    RateLimitError,
    TinyFish,
)
from tinyfish.search.types import SearchQueryResponse

from app.core.exceptions import ConfigurationError
from app.integrations.tinyfish import (
    TinyFishAdapter,
    TinyFishAuthenticationError,
    TinyFishConnectionError,
    TinyFishInvalidResponseError,
    TinyFishProviderError,
    TinyFishRateLimitError,
    TinyFishTimeoutError,
)


def factory_with(response=None, error=None):
    client = Mock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    client.search.query = AsyncMock(side_effect=error)
    client.search.query.return_value = response
    return Mock(return_value=client), client


def result(**changes):
    values = dict(
        query="Python",
        total_results=1,
        page=0,
        results=[
            dict(
                position=1,
                site_name="canonical.com",
                title="Intern",
                snippet="Evidence",
                url="https://canonical.com/careers/123",
            )
        ],
    )
    values.update(changes)
    return SearchQueryResponse.model_validate(values)


def test_success_contract_country_vs_city_and_sdk_retry_disabled(discovery_settings):
    factory, client = factory_with(result())
    adapter = TinyFishAdapter(discovery_settings, client_factory=factory)
    records = adapter.search("Python", location="Delhi NCR")
    assert records[0].verification_status == "unverified"
    assert records[0].verified_at is None
    assert adapter.attempt_count == 1
    assert factory.call_args.kwargs["max_retries"] == 0
    assert factory.call_args.kwargs["base_url"] is None
    assert client.search.query.call_args.args == ("Python Delhi NCR",)
    assert "location" not in client.search.query.call_args.kwargs
    assert client.search.query.call_args.kwargs["include_domains"] == "canonical.com"


def test_installed_sdk_default_and_custom_base_url_contract():
    with TinyFish(api_key="synthetic-only") as client:
        assert client.product_url("search") == "https://api.search.tinyfish.ai/"
    with TinyFish(api_key="synthetic-only", base_url="https://api.search.tinyfish.ai") as client:
        assert client.product_url("search") == "/v1/search"


@pytest.mark.parametrize(
    "base", ["https://api.search.tinyfish.ai", "https://agent.tinyfish.ai", "https://evil.invalid"]
)
def test_custom_base_url_is_not_silently_rewritten(discovery_settings, base):
    discovery_settings.tinyfish_base_url = base
    with pytest.raises(ConfigurationError):
        TinyFishAdapter(discovery_settings)


@pytest.mark.parametrize(
    "error,expected,attempts",
    [
        (
            AuthenticationError("SECRET_SENTINEL", response=httpx.Response(401)),
            TinyFishAuthenticationError,
            1,
        ),
        (
            RateLimitError("SECRET_SENTINEL", response=httpx.Response(429)),
            TinyFishRateLimitError,
            3,
        ),
        (
            InternalServerError("SECRET_SENTINEL", response=httpx.Response(500)),
            TinyFishProviderError,
            3,
        ),
        (APITimeoutError("SECRET_SENTINEL"), TinyFishTimeoutError, 3),
        (APIConnectionError("SECRET_SENTINEL"), TinyFishConnectionError, 3),
        (ValueError("SECRET_SENTINEL"), TinyFishInvalidResponseError, 1),
    ],
)
def test_errors_are_classified_bounded_and_redacted(discovery_settings, error, expected, attempts):
    factory, client = factory_with(error=error)
    adapter = TinyFishAdapter(discovery_settings, client_factory=factory, sleep=lambda _: None)
    with pytest.raises(expected) as failure:
        adapter.search("Python")
    assert client.search.query.call_count == attempts
    assert failure.value.attempts == attempts
    assert "SECRET_SENTINEL" not in str(failure.value)
    assert failure.value.__suppress_context__


@pytest.mark.parametrize(
    "response", [None, {}, Mock(model_dump=lambda: {"results": []}), result(page=1)]
)
def test_malformed_missing_and_wrong_page_responses(discovery_settings, response):
    factory, _ = factory_with(response)
    with pytest.raises(TinyFishInvalidResponseError):
        TinyFishAdapter(discovery_settings, client_factory=factory).search("Python")


def test_retry_after_is_respected_or_abandoned_never_shortened(discovery_settings):
    factory, client = factory_with(
        error=RateLimitError("safe", response=httpx.Response(429, headers={"Retry-After": "100"}))
    )
    with pytest.raises(TinyFishRateLimitError):
        TinyFishAdapter(
            discovery_settings,
            client_factory=factory,
            sleep=lambda _: pytest.fail("must not sleep/retry early"),
        ).search("Python")
    assert client.search.query.call_count == 1


def test_transient_error_can_recover(discovery_settings):
    factory, client = factory_with()
    client.search.query.side_effect = [APIConnectionError("safe"), result()]
    adapter = TinyFishAdapter(discovery_settings, client_factory=factory, sleep=lambda _: None)
    assert len(adapter.search("Python")) == 1
    assert adapter.attempt_count == 2
