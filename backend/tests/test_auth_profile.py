import jwt
import pytest
from fastapi import HTTPException

from app.core.config import Settings, get_settings
from app.core.security import verify_supabase_token


def token(user_id: str = "user-1") -> str:
    return jwt.encode(
        {
            "sub": user_id,
            "email": f"{user_id}@example.com",
            "aud": "authenticated",
            "iss": get_settings().jwt_issuer,
            "exp": 4102444800,
        },
        "test-secret",
        algorithm="HS256",
    )


def test_profile_requires_authentication(client):
    response = client.get("/api/v1/career-profile")
    assert response.status_code == 401


def test_profile_is_owned_by_authenticated_identity(client):
    headers = {"Authorization": f"Bearer {token()}"}
    update = {
        "summary": "Backend engineer",
        "career_stage": "early-career",
        "completion_percent": 40,
    }
    response = client.put("/api/v1/career-profile", json=update, headers=headers)
    assert response.status_code == 200
    assert response.json()["user_id"] == "user-1"

    response = client.get("/api/v1/career-profile", headers=headers)
    assert response.status_code == 200
    assert response.json()["summary"] == "Backend engineer"


def test_me_derives_identity_from_token(client):
    response = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {token('user-2')}"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == "user-2"


def test_token_with_wrong_issuer_is_rejected(client):
    bad = jwt.encode(
        {"sub": "user-3", "aud": "authenticated", "iss": "wrong", "exp": 4102444800},
        "test-secret",
        algorithm="HS256",
    )
    with pytest.raises(HTTPException):
        verify_supabase_token(
            bad,
            Settings(
                supabase_jwt_secret="test-secret", supabase_jwt_issuer="https://issuer.example"
            ),
        )
