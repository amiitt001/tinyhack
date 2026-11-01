"""Source registry for opportunity discovery.

Design principles
-----------------
* Each source has explicit policy metadata: enabled/disabled/restricted.
* Only ``official_company_careers`` is fully implemented for Milestone 4.
* Remaining sources are registered but marked as ``restricted`` or
  ``unsupported`` with documented reasons.  This prevents silently attempting
  to access sources that require authentication, have CAPTCHA protection, or
  whose scraping is restricted by their terms of service.
* TinyFish domain inclusion is used to bias search results toward known
  career-page domains when using the ``official_company_careers`` source.
* This registry is not user-configurable — users may request from the
  ``sources`` list but cannot inject arbitrary domains or base URLs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SourceStatus(str, Enum):
    """Lifecycle status of a discovery source."""

    enabled = "enabled"
    disabled = "disabled"
    restricted = "restricted"
    unavailable = "unavailable"


@dataclass(frozen=True)
class SourcePolicy:
    """All metadata governing how a source may be used.

    Attributes:
        key:                  Internal identifier (used in API requests).
        display_name:         Human-readable name.
        status:               Whether this source is usable.
        supported_behavior:   What the source can actually do.
        allowed_domains:      Domain allow-list for TinyFish ``include_domains``.
        access_restriction:   Description of access limitations.
        validation_policy:    How results must be validated.
        attribution_rules:    How results must be attributed.
        reason:               Why the source is restricted/disabled, if applicable.
    """

    key: str
    display_name: str
    status: SourceStatus
    supported_behavior: str
    allowed_domains: list[str] = field(default_factory=list)
    access_restriction: str = ""
    validation_policy: str = ""
    attribution_rules: str = ""
    reason: str = ""

    @property
    def is_usable(self) -> bool:
        return self.status == SourceStatus.enabled

    def domain_include_param(self) -> str | None:
        """Return comma-separated allowed domains for TinyFish include_domains."""
        if not self.allowed_domains:
            return None
        return ",".join(self.allowed_domains)


# ---------------------------------------------------------------------------
# Source definitions
# ---------------------------------------------------------------------------

OFFICIAL_COMPANY_CAREERS = SourcePolicy(
    key="official_company_careers",
    display_name="Official Company Career Pages",
    status=SourceStatus.enabled,
    supported_behavior=(
        "TinyFish web search returns links to company career pages and job "
        "listing pages. Results are treated as unverified search snippets — "
        "the snippet and title are extracted; the full detail page is not "
        "fetched in Milestone 4. Fields unavailable from the snippet remain null."
    ),
    allowed_domains=[
        "careers.google.com",
        "jobs.lever.co",
        "boards.greenhouse.io",
        "apply.workable.com",
        "jobs.ashbyhq.com",
        "smartrecruiters.com",
        "myworkdayjobs.com",
        "taleo.net",
    ],
    access_restriction="Public career pages accessible via web search.",
    validation_policy=(
        "URL must be HTTPS, must match an allowed domain pattern, must not be a "
        "search-engine results page, and snippet must mention employment keywords."
    ),
    attribution_rules="Attribute to source company career page with original URL.",
)

LINKEDIN_JOBS = SourcePolicy(
    key="linkedin_jobs",
    display_name="LinkedIn Jobs",
    status=SourceStatus.restricted,
    supported_behavior="Not supported in Milestone 4.",
    access_restriction=(
        "LinkedIn job listings require authentication to view full details. "
        "Scraping LinkedIn is prohibited by LinkedIn's User Agreement §8.2. "
        "LinkedIn's robots.txt disallows crawling of job listings. "
        "The public search API is not available in TinyFish search scope."
    ),
    reason=(
        "Accessing LinkedIn job listings programmatically violates LinkedIn's "
        "Terms of Service and requires authenticated API access (LinkedIn Jobs API) "
        "which requires a separate partnership agreement."
    ),
)

INTERNSHALA = SourcePolicy(
    key="internshala",
    display_name="Internshala",
    status=SourceStatus.restricted,
    supported_behavior="Not supported in Milestone 4.",
    access_restriction=(
        "Internshala listing pages may be publicly accessible but full application "
        "workflows require registration. Programmatic scraping is not explicitly "
        "permitted by their terms. Implementation deferred pending ToS review."
    ),
    reason=(
        "Terms of service review required before enabling. "
        "Deferred to a future milestone after legal clearance."
    ),
)

NAUKRI = SourcePolicy(
    key="naukri",
    display_name="Naukri.com",
    status=SourceStatus.restricted,
    supported_behavior="Not supported in Milestone 4.",
    access_restriction=(
        "Naukri.com requires user registration to view full job descriptions. "
        "Automated access is restricted by their robots.txt and terms of service."
    ),
    reason=(
        "Naukri.com prohibits automated scraping. Access requires authentication. "
        "Deferred to a future milestone."
    ),
)

WELLFOUND = SourcePolicy(
    key="wellfound",
    display_name="Wellfound (AngelList Talent)",
    status=SourceStatus.restricted,
    supported_behavior="Not supported in Milestone 4.",
    access_restriction=(
        "Wellfound job detail pages require account login. "
        "Automated scraping is restricted by their terms of service."
    ),
    reason=(
        "Wellfound requires authentication to view startup job details. "
        "Deferred to a future milestone."
    ),
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, SourcePolicy] = {
    s.key: s
    for s in [
        OFFICIAL_COMPANY_CAREERS,
        LINKEDIN_JOBS,
        INTERNSHALA,
        NAUKRI,
        WELLFOUND,
    ]
}


class SourceRegistry:
    """Immutable registry of discovery sources and their policies.

    Usage::

        registry = SourceRegistry()
        source = registry.get("official_company_careers")
        if source and source.is_usable:
            ...
    """

    def get(self, key: str) -> SourcePolicy | None:
        """Return the policy for a source key, or None if unknown."""
        return _REGISTRY.get(key)

    def list_all(self) -> list[SourcePolicy]:
        """Return all registered sources."""
        return list(_REGISTRY.values())

    def list_enabled(self) -> list[SourcePolicy]:
        """Return only sources that are currently enabled."""
        return [s for s in _REGISTRY.values() if s.is_usable]

    def resolve_requested(
        self, requested_keys: list[str] | None
    ) -> tuple[list[SourcePolicy], list[str]]:
        """Resolve a user-supplied list of source keys to policies.

        Returns:
            (usable_sources, rejected_keys_with_reasons)

        Unknown and restricted sources are excluded; the caller receives a
        structured explanation of what was rejected and why.
        """
        if not requested_keys:
            # Default to all enabled sources.
            return self.list_enabled(), []

        usable: list[SourcePolicy] = []
        rejected: list[str] = []

        for key in requested_keys:
            policy = _REGISTRY.get(key)
            if policy is None:
                rejected.append(f"{key}: unknown source")
            elif not policy.is_usable:
                rejected.append(f"{key}: {policy.reason or policy.status.value}")
            else:
                usable.append(policy)

        return usable, rejected


# Module-level singleton — safe to import anywhere.
source_registry = SourceRegistry()
