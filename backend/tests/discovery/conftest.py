import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db import Base


@pytest.fixture
def discovery_settings():
    return Settings(
        _env_file=None,
        app_env="test",
        auth_mode="supabase",
        supabase_url=None,
        supabase_jwt_secret="test-secret",
        supabase_jwt_issuer=None,
        supabase_jwt_jwks_url=None,
        tinyfish_base_url=None,
        tinyfish_api_key="synthetic-test-only",
        discovery_enabled=True,
        discovery_official_source_reviewed=True,
        tinyfish_retry_base_seconds=0,
    )


@pytest.fixture
def listing():
    def render(job_id="123", **changes):
        node = {
            "@context": "https://schema.org",
            "@type": "JobPosting",
            "title": "Python Developer Intern",
            "hiringOrganization": {"name": "Canonical"},
            "description": "<p>Build reliable Python services.</p>",
            "url": f"https://canonical.com/careers/{job_id}",
            "directApply": True,
            "employmentType": "INTERN",
            "skills": ["Python", " SQL ", "python"],
            "jobLocation": {"address": {"addressLocality": "Delhi NCR", "addressCountry": "IN"}},
        }
        node.update(changes)
        return f'<html><script type="application/ld+json">{json.dumps(node)}</script></html>'

    return render


@pytest.fixture(scope="session")
def migrated_postgres():
    url = os.environ.get("DISCOVERY_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set DISCOVERY_TEST_DATABASE_URL to an isolated skillsphere_m4_test database")
    parsed = make_url(url)
    if parsed.get_backend_name() != "postgresql" or not (parsed.database or "").startswith(
        "skillsphere_m4_test"
    ):
        pytest.fail("Refusing migration tests outside a dedicated skillsphere_m4_test database")
    backend = Path(__file__).resolve().parents[2]
    env = {**os.environ, "DATABASE_URL": url}
    for revision in ["0004_career_analysis_idempotency"]:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", revision],
            cwd=backend,
            env=env,
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            "Historical PostgreSQL migrations failed (no connection data logged)"
        )
    engine = create_engine(url)
    sentinel = uuid.uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO opportunities (id,title,source_url,status) VALUES (:id,'Preserved legacy listing',:url,'unverified')"
            ),
            {"id": sentinel, "url": f"https://legacy.invalid/{sentinel}"},
        )
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=backend,
        env=env,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, "Milestone 4 migration failed (no connection data logged)"
    with engine.connect() as connection:
        assert (
            connection.scalar(
                text("SELECT title FROM opportunities WHERE id=:id"), {"id": sentinel}
            )
            == "Preserved legacy listing"
        )
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version"))
            == "0005_opportunity_discovery"
        )
    yield engine
    engine.dispose()


@pytest.fixture(params=["sqlite", "postgresql"])
def discovery_db(request):
    if request.param == "postgresql":
        engine = request.getfixturevalue("migrated_postgres")
    else:
        engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    if request.param == "sqlite":
        engine.dispose()
