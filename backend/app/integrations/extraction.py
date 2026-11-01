"""Opportunity extraction, validation, and normalisation.

Responsibilities
----------------
* Validate a TinyFish search result against source policy.
* Extract typed opportunity fields from the search snippet.
* Normalise text fields (whitespace, employment type, work mode).
* Compute a deterministic content fingerprint for deduplication.
* Reject records that fail validation with structured rejection reasons.

Design rules (from milestone spec)
------------------------------------
1. Never invent missing fields — null stays null.
2. Do not infer salary or deadline without evidence in the snippet.
3. Validate URL structure and source-domain association.
4. Reject malformed records; track rejection reasons.
5. Bound all text and payload sizes.
6. Do not pass unrestricted HTML/text to Gemini.
7. Treat all scraped content as untrusted data.
8. A search-result URL alone is NOT sufficient evidence of a valid listing.
   The extraction_status remains "unextracted" in Milestone 4 because full
   detail-page fetching is not implemented yet.
"""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime

from app.integrations.source_registry import SourcePolicy
from app.integrations.tinyfish import SearchResultItem
from app.integrations.url_safety import (
    MAX_CONTENT_LENGTH,
    validate_scraped_content,
    validate_url,
)

logger = logging.getLogger(__name__)

# Employment keywords used to loosely validate that a snippet is job-related.
_EMPLOYMENT_KEYWORDS: frozenset[str] = frozenset(
    {
        "job",
        "jobs",
        "career",
        "careers",
        "position",
        "vacancy",
        "vacancies",
        "opening",
        "hiring",
        "hire",
        "apply",
        "application",
        "internship",
        "intern",
        "role",
        "roles",
        "opportunity",
        "opportunities",
        "engineer",
        "developer",
        "analyst",
        "manager",
        "associate",
        "graduate",
        "fresher",
        "junior",
        "senior",
    }
)

_EMPLOYMENT_TYPE_MAP: dict[str, str] = {
    "full-time": "fulltime",
    "full time": "fulltime",
    "fulltime": "fulltime",
    "part-time": "parttime",
    "part time": "parttime",
    "parttime": "parttime",
    "internship": "internship",
    "intern": "internship",
    "contract": "contract",
    "contractor": "contract",
    "freelance": "contract",
    "temporary": "contract",
}

_WORK_MODE_MAP: dict[str, str] = {
    "remote": "remote",
    "work from home": "remote",
    "wfh": "remote",
    "hybrid": "hybrid",
    "on-site": "onsite",
    "on site": "onsite",
    "onsite": "onsite",
    "in-office": "onsite",
    "in office": "onsite",
}


@dataclass
class NormalisedOpportunity:
    """Validated, normalised opportunity extracted from a search result.

    Fields that cannot be determined from the snippet remain ``None``.
    ``extraction_status`` is always "unextracted" in Milestone 4 because
    the full detail page is not fetched.
    """

    title: str
    company_name: str | None
    description: str | None  # snippet text (bounded, sanitised)
    location: str | None
    work_mode: str | None
    employment_type: str | None
    experience_requirement: str | None
    required_skills: list[str]
    preferred_skills: list[str]
    salary_min: float | None
    salary_max: float | None
    salary_currency: str | None
    stipend: str | None
    application_url: str | None  # canonical application URL if extractable
    canonical_url: str
    source_url: str  # original unmodified URL from search result
    source_attribution: str  # source policy key
    discovered_at: datetime
    # Milestone 4 limitation: detail page is not fetched.
    extraction_status: str = "unextracted"
    # Deterministic fingerprint for deduplication.
    content_hash: str = ""

    # Raw payload (bounded title + snippet for provenance).
    raw_payload: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ExtractionResult:
    """Outcome of an extraction attempt."""

    success: bool
    opportunity: NormalisedOpportunity | None
    rejection_reason: str | None


def _normalise_employment_type(text: str) -> str | None:
    lower = text.lower()
    for keyword, normalized in _EMPLOYMENT_TYPE_MAP.items():
        if keyword in lower:
            return normalized
    return None


def _normalise_work_mode(text: str) -> str | None:
    lower = text.lower()
    for keyword, normalized in _WORK_MODE_MAP.items():
        if keyword in lower:
            return normalized
    return None


def _is_employment_related(text: str) -> bool:
    """Loosely check whether the snippet mentions employment concepts."""
    lower = text.lower()
    return any(kw in lower for kw in _EMPLOYMENT_KEYWORDS)


def _compute_content_hash(canonical_url: str) -> str:
    """Deterministic fingerprint based on the canonical URL."""
    return hashlib.sha256(canonical_url.encode()).hexdigest()[:64]


def _normalise_title(title: str) -> str:
    """Strip excessive whitespace and cap title length."""
    return re.sub(r"\s+", " ", title).strip()[:512]


def extract_opportunity(
    result: SearchResultItem,
    source_policy: SourcePolicy,
) -> ExtractionResult:
    """Extract and validate a normalised opportunity from a search result.

    Args:
        result: Typed search result from the TinyFish adapter.
        source_policy: The source policy governing this result.

    Returns:
        ``ExtractionResult`` with either a valid opportunity or a rejection reason.
    """
    # --- 1. URL validation ------------------------------------------------
    url_check = validate_url(
        result.url,
        allowed_domains=source_policy.allowed_domains if source_policy.allowed_domains else None,
    )
    if not url_check.is_valid:
        logger.debug("URL rejected url=%r reason=%s", result.url, url_check.rejection_reason)
        return ExtractionResult(False, None, f"URL rejected: {url_check.rejection_reason}")

    canonical_url = url_check.canonical_url or result.url

    # --- 2. Title validation ----------------------------------------------
    title_check = validate_scraped_content(result.title, field_name="title")
    if not title_check.is_safe or not title_check.sanitised_text:
        return ExtractionResult(False, None, f"Title rejected: {title_check.rejection_reason}")
    normalised_title = _normalise_title(title_check.sanitised_text)
    if not normalised_title:
        return ExtractionResult(False, None, "Title is empty after normalisation")

    # --- 3. Snippet validation --------------------------------------------
    snippet_check = validate_scraped_content(
        result.snippet,
        field_name="snippet",
        max_length=MAX_CONTENT_LENGTH,
    )
    # A failed snippet check is not a hard rejection — log and set to None.
    description: str | None = None
    if snippet_check.is_safe:
        description = snippet_check.sanitised_text
    else:
        logger.debug(
            "Snippet rejected url=%r reason=%s", result.url, snippet_check.rejection_reason
        )

    # --- 4. Employment keyword check (soft validation) -------------------
    combined_text = f"{normalised_title} {description or ''}".lower()
    if not _is_employment_related(combined_text):
        return ExtractionResult(
            False,
            None,
            "Result does not appear to be a job/internship listing (no employment keywords found)",
        )

    # --- 5. Field extraction from snippet (no fabrication) ---------------
    employment_type: str | None = None
    work_mode: str | None = None
    if description:
        employment_type = _normalise_employment_type(description) or _normalise_employment_type(
            normalised_title
        )
        work_mode = _normalise_work_mode(description) or _normalise_work_mode(normalised_title)

    # Search metadata does not prove the employer or application destination.
    company_name = None
    application_url: str | None = None

    # Build bounded raw payload for provenance (no secrets, no full HTML).
    raw_payload: dict = {
        "position": result.position,
        "title": normalised_title[:256],
        "snippet": (description or "")[:512],
        "site_name": result.site_name[:128],
        "date": result.date,
        "publisher": result.publisher,
    }

    content_hash = _compute_content_hash(canonical_url)

    opportunity = NormalisedOpportunity(
        title=normalised_title,
        company_name=company_name,
        description=description,
        location=None,  # not available from search snippet
        work_mode=work_mode,
        employment_type=employment_type,
        experience_requirement=None,  # not available from search snippet
        required_skills=[],
        preferred_skills=[],
        salary_min=None,
        salary_max=None,
        salary_currency=None,
        stipend=None,
        application_url=application_url,
        canonical_url=canonical_url,
        source_url=result.url,
        source_attribution=source_policy.key,
        discovered_at=result.discovered_at,
        extraction_status="unextracted",
        content_hash=content_hash,
        raw_payload=raw_payload,
    )

    return ExtractionResult(True, opportunity, None)


def extract_opportunities(
    results: list[SearchResultItem],
    source_policy: SourcePolicy,
) -> tuple[list[NormalisedOpportunity], list[tuple[str, str]]]:
    """Extract and validate all results from a TinyFish search response.

    Args:
        results: Raw search result items from the adapter.
        source_policy: The source policy governing these results.

    Returns:
        (accepted_opportunities, rejection_records)
        where rejection_records is a list of (url, reason) tuples.
    """
    accepted: list[NormalisedOpportunity] = []
    rejected: list[tuple[str, str]] = []

    for result in results:
        outcome = extract_opportunity(result, source_policy)
        if outcome.success and outcome.opportunity:
            accepted.append(outcome.opportunity)
        else:
            rejected.append((result.url, outcome.rejection_reason or "unknown"))

    logger.info("Extraction complete: accepted=%d rejected=%d", len(accepted), len(rejected))
    return accepted, rejected
