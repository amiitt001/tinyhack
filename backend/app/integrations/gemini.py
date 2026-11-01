import json
from dataclasses import dataclass

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, IntegrationError
from app.schemas.career import CareerAnalysisOutput


@dataclass(frozen=True)
class CareerAnalysis:
    output: CareerAnalysisOutput
    limitations: list[str]
    attempts: int = 1


class GeminiCareerAnalyzer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if not settings.gemini_api_key:
            raise ConfigurationError("GEMINI_API_KEY is not configured")

    def analyze(self, profile_summary: str) -> CareerAnalysis:
        try:
            from google import genai

            client = genai.Client(api_key=self.settings.gemini_api_key)
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=(
                    "Analyze this career profile. Do not invent facts. Return concise "
                    "career directions and explicitly state limitations.\n\n"
                    f"Profile:\n{profile_summary}"
                ),
                config={
                    "response_mime_type": "application/json",
                    "response_schema": CareerAnalysisOutput.model_json_schema(),
                },
            )
            output = CareerAnalysisOutput.model_validate(json.loads(response.text or "{}"))
            return CareerAnalysis(output=output, limitations=output.limitations)
        except Exception as exc:
            raise IntegrationError("Gemini career analysis failed") from exc
