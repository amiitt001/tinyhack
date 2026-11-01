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

    def coach(self, message: str, profile_summary: str = "") -> str:
        """Answer one grounded coaching question using the configured Gemini model."""
        try:
            from google import genai

            client = genai.Client(api_key=self.settings.gemini_api_key)
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=(
                    "You are a practical AI career coach. Use only the supplied profile "
                    "facts, do not invent experience, and give concise actionable advice. "
                    "If the profile is incomplete, say what is missing.\n\n"
                    f"Profile:\n{profile_summary or 'No profile supplied.'}\n\n"
                    f"Question:\n{message}"
                ),
            )
            text = (response.text or "").strip()
            if not text:
                raise IntegrationError("Gemini returned an empty coaching response")
            return text
        except IntegrationError:
            raise
        except Exception as exc:
            raise IntegrationError("Gemini career coaching failed") from exc

    def compare_careers(
        self, first_career: str, second_career: str, profile_summary: str = ""
    ) -> dict:
        try:
            from google import genai

            client = genai.Client(api_key=self.settings.gemini_api_key)
            response = client.models.generate_content(
                model=self.settings.gemini_model,
                contents=(
                    "Compare exactly these two career paths for the user. Use only supplied "
                    "profile facts, do not invent experience, and return practical guidance.\n\n"
                    f"Profile:\n{profile_summary or 'No profile supplied.'}\n\n"
                    f"Career A: {first_career}\nCareer B: {second_career}"
                ),
                config={
                    "response_mime_type": "application/json",
                    "response_schema": {
                        "type": "OBJECT",
                        "properties": {
                            "summary": {"type": "STRING"},
                            "career_a_fit": {"type": "STRING"},
                            "career_b_fit": {"type": "STRING"},
                            "shared_skills": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "tradeoffs": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "recommended_next_step": {"type": "STRING"},
                            "limitations": {"type": "ARRAY", "items": {"type": "STRING"}},
                        },
                        "required": [
                            "summary",
                            "career_a_fit",
                            "career_b_fit",
                            "shared_skills",
                            "tradeoffs",
                            "recommended_next_step",
                            "limitations",
                        ],
                    },
                },
            )
            result = json.loads(response.text or "{}")
            if not isinstance(result, dict):
                raise IntegrationError("Gemini returned an invalid career comparison")
            return result
        except IntegrationError:
            raise
        except Exception as exc:
            raise IntegrationError("Gemini career comparison failed") from exc
