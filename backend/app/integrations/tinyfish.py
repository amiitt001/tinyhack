from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, IntegrationError


@dataclass(frozen=True)
class SourceRecord:
    title: str
    url: str
    source: str
    discovered_at: datetime
    verified_at: datetime | None
    verification_status: str


class TinyFishAdapter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if not settings.tinyfish_api_key:
            raise ConfigurationError("TINYFISH_API_KEY is not configured")

    def search(self, query: str, *, location: str | None = None) -> list[SourceRecord]:
        try:
            from tinyfish import TinyFish

            client = TinyFish(
                api_key=self.settings.tinyfish_api_key,
                base_url=self.settings.tinyfish_base_url,
            )
            response = client.search.query(query, location=location, language="en")
            now = datetime.now(UTC)
            return [
                SourceRecord(
                    title=result.title,
                    url=result.url,
                    source="tinyfish_search",
                    discovered_at=now,
                    verified_at=None,
                    verification_status="unverified",
                )
                for result in response.results
            ]
        except Exception as exc:
            raise IntegrationError("TinyFish search failed") from exc
