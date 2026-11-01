"""URL safety validation and scraped-content prompt-injection protection.

Security invariants enforced here
----------------------------------
1. External URLs must be HTTPS.
2. External URLs must not target localhost, loopback, private, or link-local
   IP ranges (SSRF protection).
3. External URLs must not target invalid or reserved hostnames.
4. External URLs must not exceed a configurable maximum length.
5. Only URLs whose hostname matches an approved source-domain pattern are
   accepted for opportunity results.
6. All scraped text is treated as untrusted data.
7. Scraped text is sanitised and bounded before any further processing.
8. Scraped text MUST NOT be able to modify system instructions, agent
   behaviour, destination URLs, or tool selections.

Design notes
------------
* No live HTTP fetch is performed in this module — it validates URLs
  structurally and against policy.
* The ``PRIVATE_NETWORKS`` tuple covers RFC 1918, loopback (127.x, ::1),
  link-local (169.254.x, fe80::/10), and documentation ranges.
* DNS rebinding protection: hostname is validated structurally; no DNS
  resolution is performed here (resolver-level protection is an infrastructure
  concern outside the adapter scope).
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

# Maximum URL length accepted from any external source.
MAX_URL_LENGTH: int = 2048

# Maximum snippet/description text length stored or processed.
MAX_CONTENT_LENGTH: int = 4096

# Hostnames that are always rejected regardless of source policy.
_BLOCKED_HOSTNAMES: frozenset[str] = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "ip6-localhost",
        "ip6-loopback",
        "",  # bare scheme or empty host
    }
)

# Private, loopback, link-local, and reserved IP ranges (SSRF protection).
_PRIVATE_NETWORKS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local
    ipaddress.ip_network("::1/128"),  # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),  # IPv6 ULA
    ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
    ipaddress.ip_network("100.64.0.0/10"),  # carrier-grade NAT
    ipaddress.ip_network("192.0.2.0/24"),  # TEST-NET-1
    ipaddress.ip_network("198.51.100.0/24"),  # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),  # TEST-NET-3
    ipaddress.ip_network("0.0.0.0/8"),  # "this" network
    ipaddress.ip_network("240.0.0.0/4"),  # reserved
    ipaddress.ip_network("255.255.255.255/32"),  # broadcast
)

# Prompt-injection marker patterns — if any of these appear in scraped text
# the content is rejected outright to prevent LLM instruction hijacking.
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bignore\s+(all\s+)?previous\s+instructions?\b", re.IGNORECASE),
    re.compile(r"\bforget\s+(all\s+)?previous\s+instructions?\b", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+now\b.*\bassistant\b", re.IGNORECASE),
    re.compile(r"\bsystem\s*:\s*\[", re.IGNORECASE),
    re.compile(r"<\s*system\s*>", re.IGNORECASE),
    re.compile(r"\[\s*INST\s*\]", re.IGNORECASE),
    re.compile(r"\bDAN\s+mode\b", re.IGNORECASE),
    re.compile(r"\bdo\s+anything\s+now\b", re.IGNORECASE),
    re.compile(r"\bjailbreak\b", re.IGNORECASE),
    re.compile(r"\bprompt\s+injection\b", re.IGNORECASE),
]


@dataclass(frozen=True)
class URLValidationResult:
    is_valid: bool
    canonical_url: str | None
    rejection_reason: str | None


def _is_private_ip(hostname: str) -> bool:
    """Return True if the hostname resolves to a private/loopback/link-local address."""
    try:
        addr = ipaddress.ip_address(hostname)
        return any(addr in net for net in _PRIVATE_NETWORKS)
    except ValueError:
        # Not a bare IP address — do structural hostname checks only.
        return False


def validate_url(
    url: str,
    *,
    allowed_domains: list[str] | None = None,
    max_length: int = MAX_URL_LENGTH,
) -> URLValidationResult:
    """Validate a URL for structural correctness and SSRF safety.

    Args:
        url: The URL to validate.
        allowed_domains: Optional list of approved domain suffixes.
            If ``None``, domain checking is skipped (any HTTPS domain accepted).
        max_length: Maximum URL length in characters.

    Returns:
        ``URLValidationResult`` with ``is_valid``, ``canonical_url``,
        and ``rejection_reason``.
    """
    if not url or not isinstance(url, str):
        return URLValidationResult(False, None, "URL is empty or not a string")

    if len(url) > max_length:
        return URLValidationResult(
            False, None, f"URL exceeds maximum length of {max_length} characters"
        )

    try:
        parsed = urlparse(url)
    except Exception:
        return URLValidationResult(False, None, "URL cannot be parsed")

    # HTTPS only.
    if parsed.scheme.lower() != "https":
        return URLValidationResult(
            False, None, f"URL scheme {parsed.scheme!r} is not allowed; only HTTPS is accepted"
        )

    hostname = (parsed.hostname or "").lower().strip()

    if not hostname:
        return URLValidationResult(False, None, "URL has no hostname")

    if hostname in _BLOCKED_HOSTNAMES:
        return URLValidationResult(False, None, f"Hostname {hostname!r} is not permitted")

    # Reject bare IP addresses that fall in private ranges.
    if _is_private_ip(hostname):
        return URLValidationResult(
            False, None, f"URL targets a private or reserved IP address: {hostname}"
        )

    # Domain allow-list check (suffix match).
    if allowed_domains:
        matched = any(hostname == d or hostname.endswith(f".{d}") for d in allowed_domains)
        if not matched:
            return URLValidationResult(
                False,
                None,
                f"Hostname {hostname!r} is not in the approved domain list for this source",
            )

    # Reconstruct canonical URL (strip fragment; normalise scheme to lowercase).
    canonical = urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            parsed.query,
            "",  # strip fragment — not needed for job listings
        )
    )

    return URLValidationResult(True, canonical, None)


def normalize_url(url: str) -> str:
    """Produce a normalised canonical URL for deduplication.

    * Lower-cases scheme and host.
    * Removes fragment identifier.
    * Does NOT strip query parameters (many ATS systems use them to identify jobs).
    * Preserves the original path case (some ATS paths are case-sensitive).

    The original URL is always stored separately; this canonical form is used
    only for deduplication fingerprinting.
    """
    try:
        parsed = urlparse(url)
        return urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path,
                parsed.params,
                parsed.query,
                "",
            )
        )
    except Exception:
        return url


# ---------------------------------------------------------------------------
# Content safety
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ContentValidationResult:
    is_safe: bool
    sanitised_text: str | None
    rejection_reason: str | None


def validate_scraped_content(
    text: str | None,
    *,
    max_length: int = MAX_CONTENT_LENGTH,
    field_name: str = "content",
) -> ContentValidationResult:
    """Validate and sanitise untrusted scraped text.

    Enforces the invariant:
    "Webpage content must never modify system instructions, agent policies,
    tools, credentials, or destination URLs."

    Args:
        text: Raw text from an external source.
        max_length: Maximum character length after sanitisation.
        field_name: Name of the field (for error messages).

    Returns:
        ``ContentValidationResult`` with sanitised text or rejection reason.
    """
    if text is None:
        return ContentValidationResult(True, None, None)

    if not isinstance(text, str):
        return ContentValidationResult(
            False, None, f"{field_name}: expected string, got {type(text).__name__}"
        )

    # Check for prompt-injection patterns before any further processing.
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            return ContentValidationResult(
                False,
                None,
                f"{field_name}: content contains a potential prompt-injection pattern",
            )

    # Normalise whitespace (collapse multiple spaces/newlines, strip).
    sanitised = re.sub(r"\s+", " ", text).strip()

    # Enforce length limit after normalisation.
    if len(sanitised) > max_length:
        sanitised = sanitised[:max_length]

    return ContentValidationResult(True, sanitised, None)
