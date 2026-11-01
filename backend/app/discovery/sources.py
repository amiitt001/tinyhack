from dataclasses import dataclass
from typing import Literal

from app.core.config import Settings
from app.discovery.errors import DiscoveryError


@dataclass(frozen=True)
class SourcePolicy:
    name: str
    allowed_domains: tuple[str, ...]
    company: str | None
    supported: bool
    restriction: Literal["restricted", "unavailable"] | None = None
    behavior: str = "search_then_jsonld_detail"
    attribution: str = "Original URL and each accepted source observation are preserved."


OFFICIAL = SourcePolicy("official_company_careers", ("canonical.com",), "Canonical", True)
REGISTRY = {
    OFFICIAL.name: OFFICIAL,
    "linkedin_jobs": SourcePolicy(
        "linkedin_jobs", ("www.linkedin.com",), None, False, "restricted"
    ),
    "internshala": SourcePolicy("internshala", ("internshala.com",), None, False, "restricted"),
    "naukri": SourcePolicy("naukri", ("www.naukri.com",), None, False, "restricted"),
    "wellfound": SourcePolicy("wellfound", ("wellfound.com",), None, False, "unavailable"),
}


def source_status(
    policy: SourcePolicy, settings: Settings
) -> Literal["configured", "supported", "enabled", "disabled", "restricted", "unavailable"]:
    if policy.restriction:
        return policy.restriction
    if not settings.discovery_official_source_reviewed:
        return "configured"
    if not settings.discovery_enabled:
        return "disabled"
    return "enabled"


def require_sources(names: list[str], settings: Settings) -> list[SourcePolicy]:
    policies = []
    for name in names:
        policy = REGISTRY.get(name)
        if policy is None:
            raise DiscoveryError("unsupported_source", "Unknown discovery source", 422)
        status = source_status(policy, settings)
        if not policy.supported or status != "enabled":
            raise DiscoveryError(f"source_{status}", f"Source {name} is {status}", 422)
        policies.append(policy)
    return policies
