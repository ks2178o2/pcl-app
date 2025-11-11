import os
import types
import pytest
from fastapi.testclient import TestClient


# Import app and target functions
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app
from api import analysis_api


class _Resp:
    def __init__(self, status_code=200, json_data=None, text="OK"):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text

    def raise_for_status(self):
        import requests
        if 400 <= self.status_code:
            e = requests.exceptions.HTTPError(response=types.SimpleNamespace(status_code=self.status_code))
            raise e

    def json(self):
        return self._json


def test_openai_retries_then_succeeds(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    attempts = {"count": 0}

    def fake_post(url, json, headers, timeout):  # noqa: A002 - shadow builtins in tests is fine
        attempts["count"] += 1
        # First call returns 429, second returns success
        if attempts["count"] == 1:
            return _Resp(status_code=429)
        return _Resp(status_code=200, json_data={"choices": [{"message": {"content": "{\n  \"summary\": \"ok\"\n}"}}]})

    import requests
    monkeypatch.setattr(requests, "post", fake_post)

    # Reduce waits in tests
    monkeypatch.setenv("ANALYSIS_MAX_RETRIES", "2")
    monkeypatch.setenv("ANALYSIS_BASE_RETRY_DELAY", "0.01")
    content = analysis_api._analyze_with_openai("hi")
    assert "{" in content
    assert attempts["count"] == 2


def test_gemini_retries_then_succeeds(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "gk-test")

    attempts = {"count": 0}

    def fake_post(url, json, headers, timeout):  # noqa: A002
        attempts["count"] += 1
        if attempts["count"] == 1:
            return _Resp(status_code=429)
        return _Resp(status_code=200, json_data={
            "candidates": [{"content": {"parts": [{"text": "{\n  \"summary\": \"ok\"\n}"}]}}]
        })

    import requests
    monkeypatch.setattr(requests, "post", fake_post)

    monkeypatch.setenv("ANALYSIS_MAX_RETRIES", "2")
    monkeypatch.setenv("ANALYSIS_BASE_RETRY_DELAY", "0.01")
    content = analysis_api._analyze_with_gemini("hi")
    assert "{" in content
    assert attempts["count"] == 2


def test_get_org_analysis_settings_tolerant_multiple_rows(monkeypatch):
    # Build a very small fake supabase client exposing the chained API used by analysis_api
    class FakeExec:
        def __init__(self, data):
            self.data = data

    class Q:
        def __init__(self, data):
            self._data = data

        def select(self, *args, **kwargs):
            return self

        def eq(self, *args, **kwargs):
            return self

        def order(self, *args, **kwargs):
            return self

        def limit(self, *args, **kwargs):
            return self

        def execute(self):
            return FakeExec(self._data)

    class FakeSB:
        def table(self, name):
            assert name == "profiles"
            # Multiple rows to simulate duplicates; tolerant logic should take newest
            data = [
                {"organization_id": "org-1", "created_at": "2025-01-01T00:00:00Z"},
                {"organization_id": "org-1", "created_at": "2025-12-31T00:00:00Z"},
            ]
            return Q(data)

        def from_(self, name):
            assert name == "analysis_settings"
            data = [
                {"provider_order": ["gemini", "openai"], "enabled_providers": ["gemini", "openai"], "created_at": "2025-12-31T00:00:00Z"},
                {"provider_order": ["openai"], "enabled_providers": ["openai"], "created_at": "2025-01-01T00:00:00Z"},
            ]
            return Q(data)

    os.environ["ANALYSIS_AVAILABLE_PROVIDERS"] = "openai,gemini"
    os.environ["ANALYSIS_PROVIDER_ORDER"] = "openai,gemini"

    order, enabled = analysis_api._get_org_analysis_settings(FakeSB(), "user-1")
    # Should reflect the newest settings row
    assert order == ["gemini", "openai"]
    assert set(enabled) == {"gemini", "openai"}


def test_analyze_endpoint_ok(monkeypatch):
    # Force providers to simple deterministic return via monkeypatching wrappers
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("GOOGLE_API_KEY", "gk-test")

    def fake_openai(text):
        return "{\n \"summary\": \"ok\"\n}"

    def fake_gemini(text):
        return "{\n \"summary\": \"ok\"\n}"

    monkeypatch.setattr(analysis_api, "_analyze_with_openai", fake_openai)
    monkeypatch.setattr(analysis_api, "_analyze_with_gemini", fake_gemini)

    # Limit concurrency to 1 to exercise semaphore path
    monkeypatch.setenv("MAX_CONCURRENT_ANALYSES", "1")

    client = TestClient(app)
    # Provide minimal auth stub
    token = "dummy"
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/api/analysis/analyze", json={"prompt": "hello"}, headers=headers)
    assert resp.status_code == 200
    assert "analysis" in resp.json()


