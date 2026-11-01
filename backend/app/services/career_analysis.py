import time
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.agents.career import CareerAgent
from app.core.config import Settings
from app.core.security import AuthenticatedUser
from app.models import AgentRun, CareerAnalysis, Resume


class CareerAnalysisService:
    prompt_version = "career-analysis-v1"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.agent = CareerAgent.from_settings(settings)

    def run(self, session: Session, user: AuthenticatedUser, resume: Resume) -> CareerAnalysis:
        if resume.user_id != user.id:
            raise PermissionError("Resume does not belong to user")
        if not resume.parsed_data:
            raise ValueError("Resume must be parsed before analysis")
        existing = session.scalar(
            select(CareerAnalysis)
            .where(
                CareerAnalysis.user_id == user.id,
                CareerAnalysis.resume_id == resume.id,
                CareerAnalysis.prompt_version == self.prompt_version,
                CareerAnalysis.model_version == self.settings.gemini_model,
                CareerAnalysis.status == "succeeded",
            )
            .order_by(CareerAnalysis.created_at.desc())
        )
        if existing is not None:
            return existing
        started = time.perf_counter()
        run = AgentRun(
            id=uuid.uuid4(),
            user_id=user.id,
            workflow="career-analysis",
            status="running",
            model_version=self.settings.gemini_model,
            prompt_version=self.prompt_version,
            attempt_count=1,
        )
        session.add(run)
        try:
            result = self.agent.run(profile_summary=str(resume.parsed_data))
            run.attempt_count = result.attempts
            output = result.output
            analysis = CareerAnalysis(
                user_id=user.id,
                resume_id=resume.id,
                output=output.model_dump(),
                model_version=self.settings.gemini_model,
                prompt_version=self.prompt_version,
            )
            run.status = "succeeded"
            session.add(analysis)
            return_value = analysis
        except Exception:
            run.status = "failed"
            run.error = "Career analysis failed"
            run.duration_ms = round((time.perf_counter() - started) * 1000)
            session.commit()
            raise
        finally:
            run.duration_ms = round((time.perf_counter() - started) * 1000)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            duplicate = session.scalar(
                select(CareerAnalysis)
                .where(
                    CareerAnalysis.user_id == user.id,
                    CareerAnalysis.resume_id == resume.id,
                    CareerAnalysis.prompt_version == self.prompt_version,
                    CareerAnalysis.model_version == self.settings.gemini_model,
                    CareerAnalysis.status == "succeeded",
                )
                .order_by(CareerAnalysis.created_at.desc())
            )
            if duplicate is None:
                raise
            return duplicate
        session.refresh(return_value)
        return return_value
