"""Map user locations to TinyFish's documented country-level location filter."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchLocation:
    provider_country: str | None
    query_constraint: str | None


_INDIA_PLACES = {
    "delhi ncr",
    "delhi",
    "bengaluru",
    "bangalore",
    "hyderabad",
    "pune",
    "mumbai",
}


def map_search_location(location: str | None) -> SearchLocation:
    """Return the documented country code and any locality to add to the query.

    TinyFish Search's ``location`` filter is country-level. City names are kept
    as search terms; this does not claim city-level provider filtering.
    Unknown place names are likewise preserved in the query without guessing a
    country. A two-letter value is accepted as an explicitly supplied country
    code.
    """
    if location is None or not location.strip():
        return SearchLocation(None, None)

    value = re.sub(r"\s+", " ", location).strip()
    folded = value.casefold()
    if folded == "india":
        return SearchLocation("IN", None)
    if folded in _INDIA_PLACES:
        return SearchLocation("IN", value)
    if folded in {"remote india", "remote in india", "remote, india"}:
        return SearchLocation("IN", "remote India")
    if re.fullmatch(r"[A-Za-z]{2}", value):
        return SearchLocation(value.upper(), None)
    return SearchLocation(None, value)
