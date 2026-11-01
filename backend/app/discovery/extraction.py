"""Strict JSON-LD JobPosting extraction. External text never becomes instructions."""

import hashlib
import html
import json
import re
import unicodedata
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from urllib.parse import urlsplit

from app.discovery.errors import DiscoveryError
from app.discovery.security import MAX_PAGE_BYTES, validate_url
from app.discovery.sources import SourcePolicy


def normalized(value: str, limit: int = 255) -> str:
    if not isinstance(value, str):
        raise DiscoveryError("invalid_text", "Expected text evidence")
    text = " ".join(unicodedata.normalize("NFKC", value).split())
    if not text or len(text) > limit or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text):
        raise DiscoveryError("invalid_text", "Text is empty or exceeds field limits")
    return text


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.hidden = max(0, self.hidden - 1)

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def clean_text(value: str, limit: int = 20_000) -> str:
    if not isinstance(value, str) or len(value) > MAX_PAGE_BYTES:
        raise DiscoveryError("invalid_text", "Invalid text payload")
    parser = TextOnly()
    parser.feed(value)
    return normalized(html.unescape(" ".join(parser.parts)), limit)


class JobLDParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.collect = False
        self.chunks: list[str] = []
        self.documents: list[str] = []
        self.has_application_form = False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "script" and attributes.get("type", "").lower() == "application/ld+json":
            self.collect = True
            self.chunks = []
        if tag == "form" and attributes.get("id") in {
            "application-form",
            "application_form",
            "application",
        }:
            self.has_application_form = True

    def handle_data(self, data):
        if self.collect:
            self.chunks.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.collect:
            self.documents.append("".join(self.chunks))
            self.collect = False


def job_nodes(value):
    if isinstance(value, list):
        for item in value:
            yield from job_nodes(item)
    elif isinstance(value, dict):
        kind = value.get("@type")
        if kind == "JobPosting" or (isinstance(kind, list) and "JobPosting" in kind):
            yield value
        if "@graph" in value:
            yield from job_nodes(value["@graph"])


def skills(value) -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.split(",")
    if not isinstance(value, list) or len(value) > 50 or any(not isinstance(v, str) for v in value):
        raise DiscoveryError("invalid_skills", "Malformed skill evidence")
    return sorted({normalized(v, 128).casefold() for v in value})


def timestamp(value) -> datetime | None:
    if value is None:
        return None
    try:
        if not isinstance(value, str) or len(value) > 64:
            raise ValueError
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result.replace(tzinfo=UTC) if result.tzinfo is None else result.astimezone(UTC)
    except ValueError:
        raise DiscoveryError("invalid_deadline", "Invalid deadline evidence") from None


def money(value) -> Decimal | None:
    if value is None:
        return None
    try:
        result = Decimal(str(value))
        if not result.is_finite() or result < 0 or result > Decimal("999999999999.99"):
            raise InvalidOperation
        return result.quantize(Decimal(".01"))
    except InvalidOperation:
        raise DiscoveryError("invalid_compensation", "Invalid compensation evidence") from None


def extract_opportunity(page: str, original_url: str, policy: SourcePolicy) -> dict:
    if not isinstance(page, str) or len(page.encode()) > MAX_PAGE_BYTES:
        raise DiscoveryError("content_too_large", "Extraction content exceeds limits")
    canonical = validate_url(original_url, policy)
    parser = JobLDParser()
    parser.feed(page)
    nodes = []
    try:
        for document in parser.documents[:20]:
            nodes.extend(job_nodes(json.loads(document)))
    except (ValueError, RecursionError):
        raise DiscoveryError("invalid_jsonld", "Malformed structured listing evidence") from None
    matches = [
        node
        for node in nodes
        if isinstance(node.get("url"), str) and validate_url(node["url"], policy) == canonical
    ]
    if len(matches) != 1:
        raise DiscoveryError(
            "unsupported_extraction", "A single matching JSON-LD JobPosting is required"
        )
    node = matches[0]
    if node.get("directApply") is not True and not parser.has_application_form:
        raise DiscoveryError(
            "missing_application_evidence", "No supported application-page evidence"
        )
    title = normalized(node.get("title"), 255)
    company = node.get("hiringOrganization")
    if not isinstance(company, dict) or not isinstance(company.get("name"), str):
        raise DiscoveryError("missing_company", "Company evidence is required")
    company_name = normalized(company["name"])
    if policy.company and company_name.casefold() != policy.company.casefold():
        raise DiscoveryError("company_mismatch", "Company evidence does not match source policy")
    description = clean_text(node.get("description"))
    if re.search(
        r"ignore (?:all |previous |system )?instructions|reveal (?:the )?(?:api.key|secret)|<\|(?:system|assistant)",
        description,
        re.I,
    ):
        raise DiscoveryError(
            "untrusted_instruction_content", "Listing contains unsupported instruction-like content"
        )
    location = None
    job_location = node.get("jobLocation")
    if isinstance(job_location, list):
        if len(job_location) != 1:
            raise DiscoveryError(
                "unsupported_locations", "Multiple locations require a future extractor"
            )
        job_location = job_location[0]
    if isinstance(job_location, dict):
        address = job_location.get("address", {})
        if isinstance(address, dict):
            values = [
                address.get(k) for k in ("addressLocality", "addressRegion", "addressCountry")
            ]
            if any(v is not None and not isinstance(v, str) for v in values):
                raise DiscoveryError("invalid_location", "Invalid location evidence")
            location = normalized(", ".join(v for v in values if v)) if any(values) else None
    elif job_location is not None:
        raise DiscoveryError("invalid_location", "Invalid location evidence")
    employment = node.get("employmentType")
    if employment is not None:
        mapping = {
            "FULL_TIME": "full_time",
            "PART_TIME": "part_time",
            "INTERN": "internship",
            "CONTRACTOR": "contract",
            "TEMPORARY": "temporary",
            "VOLUNTEER": "volunteer",
            "OTHER": "other",
        }
        employment = mapping.get(normalized(employment).upper())
    deadline = timestamp(node.get("validThrough"))
    if deadline and deadline <= datetime.now(UTC):
        raise DiscoveryError("listing_expired", "Listing deadline has passed")
    salary = node.get("baseSalary")
    minimum = maximum = currency = salary_unit = None
    if salary is not None:
        if not isinstance(salary, dict) or not isinstance(salary.get("value"), dict):
            raise DiscoveryError(
                "invalid_compensation", "Structured compensation evidence required"
            )
        currency = salary.get("currency")
        if currency is not None and (
            not isinstance(currency, str) or not re.fullmatch("[A-Z]{3}", currency)
        ):
            raise DiscoveryError("invalid_compensation", "Invalid salary currency")
        if salary["value"].get("unitText") is not None:
            salary_unit = normalized(salary["value"]["unitText"], 32)
        minimum = money(salary["value"].get("minValue", salary["value"].get("value")))
        maximum = money(salary["value"].get("maxValue", salary["value"].get("value")))
        if minimum is not None and maximum is not None and minimum > maximum:
            raise DiscoveryError("invalid_compensation", "Salary range is inverted")
    identifier = node.get("identifier")
    external_id = (
        normalized(str(identifier["value"]))
        if isinstance(identifier, dict) and isinstance(identifier.get("value"), (str, int))
        else urlsplit(canonical).path.split("/")[-1]
    )
    experience = node.get("experienceRequirements")
    experience = clean_text(experience, 2000) if isinstance(experience, str) else None
    data = dict(
        title=title,
        company_name=company_name,
        description=description,
        location=location,
        employment_type=employment,
        work_mode="remote" if node.get("jobLocationType") == "TELECOMMUTE" else None,
        experience_requirement=experience,
        required_skills=skills(node.get("skills")),
        preferred_skills=None,
        salary_min=minimum,
        salary_max=maximum,
        salary_currency=currency,
        salary_unit=salary_unit,
        stipend=None,
        application_url=canonical,
        canonical_url=canonical,
        source_external_id=external_id,
        deadline=deadline,
        expires_at=deadline,
        content_hash=hashlib.sha256(page.encode()).hexdigest(),
    )
    fingerprint = [
        normalized(v).casefold() if v else None for v in (title, company_name, location, employment)
    ]
    data["fingerprint"] = hashlib.sha256(
        json.dumps(fingerprint, ensure_ascii=True).encode()
    ).hexdigest()
    return data
