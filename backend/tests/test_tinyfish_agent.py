from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.core.exceptions import (
    TinyFishInvalidResponseError,
    TinyFishProviderError,
    TinyFishTimeoutError,
)
from app.integrations.tinyfish_agent import TinyFishAgentAdapter


def _settings(**overrides):
    values = {"tinyfish_api_key": "mock", "tinyfish_agent_timeout_seconds": 10, **overrides}
    return Settings(_env_file=None, **values)


def test_agent_adapter_queues_polls_and_normalizes_result(monkeypatch):
    requested = {}
    result_payload = {"jobs": [], "execution_status": "completed", "errors": []}

    class FakeClient:
        def __init__(self, **kwargs):
            assert kwargs["timeout"] == 40
            self.agent = SimpleNamespace(queue=lambda **params: (requested.update(params) or SimpleNamespace(run_id="run-123")))
            self.runs = SimpleNamespace(get=lambda run_id: SimpleNamespace(
                status="COMPLETED", result=result_payload,
                started_at=datetime.now(UTC), finished_at=datetime.now(UTC), error=None,
            ))
            self.closed = False

        def close(self):
            self.closed = True

    clients = []
    original = FakeClient.__init__

    def init(self, **kwargs):
        original(self, **kwargs)
        clients.append(self)

    FakeClient.__init__ = init
    monkeypatch.setattr("tinyfish.TinyFish", FakeClient)
    result = TinyFishAgentAdapter(_settings()).investigate("https://jobs.lever.co/acme", max_jobs=3)
    assert requested["url"] == "https://jobs.lever.co/acme"
    assert requested["output_schema"]["properties"]["jobs"]["type"] == "array"
    assert requested["agent_config"].max_duration_seconds == 10
    assert result.run_id == "run-123"
    assert result.investigation.execution_status == "completed"
    assert result.num_of_steps is None
    assert clients[0].closed


def test_real_provider_enum_casing_is_normalized():
    from app.integrations.tinyfish_schemas import AgentInvestigation

    result = AgentInvestigation.model_validate({
        "jobs": [{
            "title": "Intern", "job_url": "https://jobs.lever.co/acme/123",
            "listing_status": "Active", "evidence": [{
                "field": "title", "value": "Intern", "evidence_url": "https://jobs.lever.co/acme/123",
                "evidence_text": "Intern", "confidence": "High",
            }], "missing_fields": [],
        }],
        "execution_status": "Completed", "errors": [],
    })
    assert result.execution_status == "completed"
    assert result.jobs[0].listing_status == "active"
    assert result.jobs[0].evidence[0].confidence == "high"


@pytest.mark.parametrize(
    ("status", "payload", "exception"),
    [
        ("FAILED", None, TinyFishProviderError),
        (
            "COMPLETED",
            {"jobs": [{"title": "Missing URL"}], "execution_status": "completed", "errors": []},
            TinyFishInvalidResponseError,
        ),
    ],
)
def test_agent_adapter_rejects_failed_or_malformed_results(monkeypatch, status, payload, exception):
    class FakeClient:
        def __init__(self, **kwargs):
            self.agent = SimpleNamespace(queue=lambda **params: SimpleNamespace(run_id="run-bad"))
            self.runs = SimpleNamespace(get=lambda run_id: SimpleNamespace(
                status=status, result=payload, started_at=None, finished_at=None, error="failed",
            ))

        def close(self):
            pass

    monkeypatch.setattr("tinyfish.TinyFish", FakeClient)
    with pytest.raises(exception):
        TinyFishAgentAdapter(_settings()).investigate("https://jobs.lever.co/acme")


def test_agent_poll_timeout_retains_provider_run_id(monkeypatch):
    class FakeClient:
        def __init__(self, **kwargs):
            self.agent = SimpleNamespace(queue=lambda **params: SimpleNamespace(run_id="run-timeout"))
            self.runs = SimpleNamespace(get=lambda run_id: SimpleNamespace(status="RUNNING"))
            self.closed = False

        def close(self):
            self.closed = True

    clients = []
    original_init = FakeClient.__init__
    def init(self, **kwargs):
        original_init(self, **kwargs)
        clients.append(self)

    monkeypatch.setattr(FakeClient, "__init__", init)
    monkeypatch.setattr("tinyfish.TinyFish", FakeClient)
    clock = iter((0.0, 41.0, 42.0))
    monkeypatch.setattr("app.integrations.tinyfish_agent.time.monotonic", lambda: next(clock))
    with pytest.raises(TinyFishTimeoutError) as caught:
        TinyFishAgentAdapter(_settings(tinyfish_agent_timeout_seconds=10)).investigate("https://jobs.lever.co/acme")
    assert caught.value.provider_run_id == "run-timeout"
    assert caught.value.started_at is not None
    assert clients[0].closed


def test_agent_adapter_requires_configuration():
    from app.core.exceptions import ConfigurationError

    with pytest.raises(ConfigurationError, match="TINYFISH_API_KEY"):
        TinyFishAgentAdapter(Settings(_env_file=None, tinyfish_api_key=""))
