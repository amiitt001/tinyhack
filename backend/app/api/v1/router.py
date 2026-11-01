from fastapi import APIRouter

from app.api.v1.endpoints import career_analysis, discovery, health, profile, resumes, users

router = APIRouter(prefix="/api/v1")
router.include_router(health.router, tags=["health"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(profile.router, tags=["career-profile"])
router.include_router(resumes.router, tags=["resumes"])
router.include_router(career_analysis.router, tags=["career-analysis"])

router.include_router(discovery.router)
