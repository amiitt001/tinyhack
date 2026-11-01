import uuid

import jwt

from app.core.config import get_settings
from app.models import CareerAnalysis, User


def test_analysis_history_is_paginated_and_user_scoped(client):
    from conftest import TestingSession

    def auth(user_id: str) -> dict[str, str]:
        token = jwt.encode(
            {
                "sub": user_id,
                "aud": "authenticated",
                "iss": get_settings().jwt_issuer,
                "exp": 4102444800,
            },
            "test-secret",
            algorithm="HS256",
        )
        return {"Authorization": f"Bearer {token}"}

    first = f"history-a-{uuid.uuid4().hex[:8]}"
    other = f"history-b-{uuid.uuid4().hex[:8]}"
    with TestingSession() as session:
        session.add_all([User(id=first), User(id=other)])
        session.flush()
        session.add(
            CareerAnalysis(
                user_id=first,
                output={"career_paths": [{"title": "Engineer", "explanation": "Grounded"}]},
                model_version="test",
                prompt_version="test",
            )
        )
        session.commit()

    response = client.get(
        "/api/v1/career-analysis?limit=1&offset=0",
        headers=auth(first),
    )
    assert response.status_code == 200
    assert response.json()[0]["career_paths"][0]["title"] == "Engineer"

    other_response = client.get(
        "/api/v1/career-analysis",
        headers=auth(other),
    )
    assert other_response.status_code == 200
    assert other_response.json() == []

    with TestingSession() as session:
        session.query(CareerAnalysis).filter(CareerAnalysis.user_id.in_([first, other])).delete()
        session.query(User).filter(User.id.in_([first, other])).delete()
        session.commit()
