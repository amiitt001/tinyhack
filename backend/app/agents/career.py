import asyncio
import json
import random
import time
from dataclasses import dataclass

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from pydantic import BaseModel

from app.core.config import Settings
from app.integrations.gemini import CareerAnalysis, GeminiCareerAnalyzer
from app.schemas.career import CareerAnalysisOutput


class CareerAnalysisInput(BaseModel):
    profile_summary: str


@dataclass
class CareerAgent:
    """Typed boundary for the first career-intelligence workflow."""

    analyzer: GeminiCareerAnalyzer

    @classmethod
    def from_settings(cls, settings: Settings) -> "CareerAgent":
        return cls(analyzer=GeminiCareerAnalyzer(settings))

    def build_adk_agent(self, settings: Settings) -> Agent:
        return Agent(
            name="career_intelligence",
            description="Provides grounded career guidance from an authorized profile.",
            model=settings.gemini_model,
            instruction=(
                "Use only facts in the supplied profile. Do not invent experience or skills. "
                "Return career_paths with title, explanation, strengths, skill_gaps, "
                "learning_priorities, and next_steps. Include limitations."
            ),
            input_schema=CareerAnalysisInput,
            output_schema=CareerAnalysisOutput,
            timeout=settings.agent_timeout_seconds,
        )

    def build_runner(self, settings: Settings) -> Runner:
        return Runner(
            app_name=settings.app_name,
            agent=self.build_adk_agent(settings),
            session_service=InMemorySessionService(),
            auto_create_session=True,
        )

    def run(self, profile_summary: str) -> CareerAnalysis:
        settings = self.analyzer.settings
        last_error: Exception | None = None
        for attempt in range(1, settings.agent_max_attempts + 1):
            try:
                result = self._run_once(profile_summary, settings)
                return CareerAnalysis(
                    output=result.output, limitations=result.limitations, attempts=attempt
                )
            except Exception as exc:
                last_error = exc
                if not self._is_retryable(exc) or attempt == settings.agent_max_attempts:
                    raise
                delay = settings.agent_retry_base_seconds * (2 ** (attempt - 1))
                time.sleep(delay + random.uniform(0, delay * 0.25))
        raise RuntimeError("ADK career workflow failed") from last_error

    def _run_once(self, profile_summary: str, settings: Settings) -> CareerAnalysis:
        async def execute() -> list:
            return await asyncio.wait_for(
                self.build_runner(settings).run_debug(
                    json.dumps({"profile_summary": profile_summary}), quiet=True
                ),
                timeout=settings.agent_timeout_seconds,
            )

        events = asyncio.run(execute())
        final_events = [event for event in events if event.is_final_response()]
        if not final_events:
            raise RuntimeError("ADK career workflow returned no final response")
        content = final_events[-1].content
        text = "".join(part.text or "" for part in content.parts if part.text)
        return CareerAnalysis(
            output=CareerAnalysisOutput.model_validate(json.loads(text)),
            limitations=[],
        )

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
            return True
        status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
        if status in {408, 429, 500, 502, 503, 504}:
            return True
        text = str(exc).upper()
        return any(
            marker in text for marker in ("408", "429", "500", "502", "503", "504", "TIMEOUT")
        )
