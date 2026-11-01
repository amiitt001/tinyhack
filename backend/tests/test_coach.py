from unittest.mock import patch

from app.core.config import Settings
from app.integrations.gemini import GeminiCareerAnalyzer


def test_coach_uses_gemini_response():
    class Response:
        text = "Focus on one portfolio project and document the outcome."

    class Models:
        def generate_content(self, **kwargs):
            return Response()

    class Client:
        models = Models()

    with patch("google.genai.Client", return_value=Client()):
        result = GeminiCareerAnalyzer(Settings(gemini_api_key="test-key")).coach(
            "Where should I focus my learning?", "Python developer"
        )

    assert result.startswith("Focus on")
