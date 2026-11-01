from fastapi import APIRouter

from app.api.v1.endpoints import (
    career_analysis,
    career_compare,
    coach,
    health,
    opportunities,
    profile,
    resumes,
    tinyfish_tools,
    users,
)

router = APIRouter(prefix="/api/v1")
router.include_router(health.router, tags=["health"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(profile.router, tags=["career-profile"])
router.include_router(resumes.router, tags=["resumes"])
router.include_router(career_analysis.router, tags=["career-analysis"])
router.include_router(career_compare.router, tags=["career-comparison"])
router.include_router(coach.router, tags=["coach"])
router.include_router(opportunities.router, tags=["opportunities"])
router.include_router(tinyfish_tools.router, tags=["opportunity-tools"])
