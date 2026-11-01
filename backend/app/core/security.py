from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from jwt import PyJWKClient

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str | None
    claims: dict


def verify_supabase_token(token: str, settings: Settings) -> AuthenticatedUser:
    if not settings.supabase_jwt_secret and not settings.supabase_jwt_jwks_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase authentication is not configured",
        )
    try:
        header = jwt.get_unverified_header(token)
        algorithm = header.get("alg")
        if algorithm == "HS256" and settings.supabase_jwt_secret:
            key = settings.supabase_jwt_secret
        elif settings.jwt_jwks_url and algorithm in {"RS256", "ES256"}:
            key = PyJWKClient(settings.jwt_jwks_url).get_signing_key_from_jwt(token).key
        else:
            raise jwt.InvalidAlgorithmError("Unsupported Supabase token algorithm")
        claims = jwt.decode(
            token,
            key,
            algorithms=[algorithm],
            audience=settings.supabase_jwt_audience,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=401, detail="Invalid token identity")
    return AuthenticatedUser(id=subject, email=claims.get("email"), claims=claims)


async def get_current_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthenticatedUser:
    authorization = request.headers.get("Authorization", "")
    scheme, _, credentials = authorization.partition(" ")
    if scheme.lower() != "bearer" or not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if settings.auth_mode == "development":
        if settings.app_env == "production":
            raise HTTPException(status_code=500, detail="Invalid authentication configuration")
        if not credentials.startswith("dev:"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Development bearer token required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = credentials.removeprefix("dev:").strip()
        if not user_id or "/" in user_id or "\\" in user_id:
            raise HTTPException(status_code=401, detail="Invalid development user")
        return AuthenticatedUser(
            id=user_id,
            email=f"{user_id}@localhost.invalid",
            claims={"sub": user_id, "auth_mode": "development"},
        )
    return verify_supabase_token(credentials, settings)
