import sys
import types

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api import analysis_api


@pytest.fixture
def analysis_client():
    app = FastAPI()
    app.include_router(analysis_api.router)
    app.dependency_overrides[analysis_api.get_current_user] = lambda: {"id": "user-123"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def _fake_getenv_factory(openai_key=None, model="gpt-4o-mini"):
    def fake_getenv(key, default=None):
        if key == "OPENAI_API_KEY":
            return openai_key
        if key == "OPENAI_MODEL":
            return model
        return default

    return fake_getenv


def test_analyze_empty_prompt_returns_400(analysis_client):
    response = analysis_client.post("/api/analysis/analyze", json={"prompt": "   "})
    assert response.status_code == 400
    assert response.json()["detail"] == "Empty prompt"


def test_analyze_uses_heuristic_when_no_key(monkeypatch, analysis_client):
    monkeypatch.setattr(analysis_api, "os", types.SimpleNamespace(getenv=_fake_getenv_factory(openai_key="")))
    payload = {"prompt": "Customer asked about pricing and timeline."}
    response = analysis_client.post("/api/analysis/analyze", json=payload)
    assert response.status_code == 200
    content = response.json()["analysis"]
    assert "Summary:" in content
    assert "pricing" in content.lower()


def test_analyze_calls_openai_when_key_present(monkeypatch, analysis_client):
    class DummyResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "AI summary content"}}]}

    monkeypatch.setattr(analysis_api, "os", types.SimpleNamespace(getenv=_fake_getenv_factory(openai_key="key-123")))
    monkeypatch.setitem(sys.modules, "requests", types.SimpleNamespace(post=lambda *a, **k: DummyResponse()))

    response = analysis_client.post("/api/analysis/analyze", json={"prompt": "Discuss renewal options"})
    assert response.status_code == 200
    assert response.json()["analysis"] == "AI summary content"


def test_analyze_falls_back_when_request_fails(monkeypatch, analysis_client):
    def failing_post(*_args, **_kwargs):
        raise RuntimeError("Network error")

    monkeypatch.setattr(analysis_api, "os", types.SimpleNamespace(getenv=_fake_getenv_factory(openai_key="key-123")))
    monkeypatch.setitem(sys.modules, "requests", types.SimpleNamespace(post=failing_post))

    payload = {"prompt": "Customer had questions about deployment timeline."}
    response = analysis_client.post("/api/analysis/analyze", json=payload)
    assert response.status_code == 200
    assert "Summary:" in response.json()["analysis"]

