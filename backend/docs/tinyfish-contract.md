# TinyFish 0.11.0 contract verification

Verification used the installed pinned SDK source and official references, not a live credential.

- [Official Search reference](https://docs.tinyfish.ai/search-api/reference)
- [Official Python package 0.11.0](https://pypi.org/project/tinyfish/0.11.0/)
- [Official Fetch reference](https://docs.tinyfish.ai/fetch-api/reference)

The installed SDK uses `GET https://api.search.tinyfish.ai/` with `X-API-Key` authentication when
`base_url=None`. An explicit base changes the product path to `/v1/search`; this is verified by an
automated installed-SDK test. The adapter rejects every nonempty custom base instead of silently
changing a legacy value. The SDK docstring suggests a free-form location, while the official Search
reference specifies a country code; this implementation puts city/location text in the query and
omits the SDK location parameter.

The adapter calls the verified `search.query` surface with plain query terms, `include_domains`,
English, web result category, and a bounded zero-based page. The provider's page maximum is 10;
application configuration limits its own discovery to at most three pages and twenty processed hits.
The response is validated using SDK `SearchQueryResponse`: query, results, total_results, page;
result URL/title/snippet lengths and result count are checked. Search results remain unverified.
No provider request ID is fabricated when the SDK result has none.

The SDK defaults to 600-second timeout and two retries. Its internal retry loop retries network
failures and 408/429/5xx with exponential waits. The adapter explicitly sets `max_retries=0` and a
bounded timeout, then owns retries, wall-clock cancellation, jitter, and Retry-After handling.
Authentication/forbidden, rate limit, timeout, connection, invalid response, and other status errors
are distinct safe exception classes. Exception text, response bodies, request objects, and headers
are not persisted or chained into the public error. Attempt counts are recorded.

The production code does not invoke Agent, browser, Fetch, Gemini, or ADK. Detail retrieval is a
separate constrained HTTPS reader because the Fetch documentation does not establish that this
application could enforce its own per-hop redirect policy or receive original JSON-LD unchanged.
A provider capability is not treated as permission to access a website. The sole implemented detail
policy remains disabled pending current source/access review and deployment verification.

**Live status: NOT TESTED.** No real TinyFish request or successful live source extraction occurred.
Mocked tests verify implementation behavior, not remote service availability or a source's terms.
