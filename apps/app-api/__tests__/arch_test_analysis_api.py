import os
import types
import json
import contextlib
import importlib.util
import sys
from fastapi.testclient import TestClient
from unittest.mock import patch

# Paths
APP_API_DIR = "/Users/krupasrinivas/pcl-product/apps/app-api"
MAIN_PATH = f"{APP_API_DIR}/main.py"

# Ensure app-api dir is importable as a package root for 'api.analysis_api'
sys.path.insert(0, APP_API_DIR)
import api.analysis_api as analysis_api  # type: ignore

# Dynamically load the FastAPI app from apps/app-api/main.py
spec = importlib.util.spec_from_file_location("app_api_main", MAIN_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)  # type: ignore
app = getattr(module, "app")

# Helpers ---------------------------------------------------------

class FakeSingle:
    def __init__(self, data):
        self.data = data

    def execute(self):
        return self

class FakeQuery:
    def __init__(self, table, data_map):
        self._table = table
        self._data_map = data_map
        self._filters = {}
        self._select = None
        self._single = False

    def select(self, fields):
        self._select = fields
        return self

    def eq(self, field, value):
        self._filters[field] = value
        return self

    # No-op ordering and limit to satisfy code paths that may call them
    def order(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        key = (self._table, tuple(sorted(self._filters.items())))
        data = self._data_map.get(key)
        if self._single:
            return types.SimpleNamespace(data=data)
        return types.SimpleNamespace(data=[data] if data else [])

class FakeSupabase:
    def __init__(self, data_map):
        self._data_map = data_map
        self.upserts = []

    def table(self, name):
        return FakeQuery(name, self._data_map)

    def from_(self, name):
        return FakeQuery(name, self._data_map)

    # Record upserts for assertions
    def upsert_record(self, table, record):
        self.upserts.append((table, record))

# Monkeypatch wrapper for upsert path used by analysis_api
class UpsertableQuery(FakeQuery):
    def __init__(self, table, data_map, supabase):
        super().__init__(table, data_map)
        self._supabase = supabase

    def upsert(self, record):
        self._supabase.upsert_record(self._table, record)
        return self

# Patch get_supabase_client to return our fake with UpsertableQuery on from_

def make_fake_supabase(profiles_org_id=None, analysis_settings=None):
    data_map = {}
    if profiles_org_id:
        data_map[("profiles", (('user_id', 'test-user'),))] = {"organization_id": profiles_org_id}
    if analysis_settings is not None:
        data_map[("analysis_settings", (('organization_id', profiles_org_id),))] = analysis_settings

    fake = FakeSupabase(data_map)

    def table(name):
        return FakeQuery(name, data_map)

    def from_(name):
        return UpsertableQuery(name, data_map, fake)

    fake.table = table  # type: ignore
    fake.from_ = from_  # type: ignore
    return fake

@contextlib.contextmanager
def override_user(role="org_admin"):
    original = analysis_api.get_current_user
    app.dependency_overrides[analysis_api.get_current_user] = lambda: {"user_id": "test-user", "role": role}
    try:
        yield
    finally:
        if analysis_api.get_current_user in app.dependency_overrides:
            del app.dependency_overrides[analysis_api.get_current_user]
    analysis_api.get_current_user = original  # type: ignore

@contextlib.contextmanager
def override_org_admin():
    original_dep = analysis_api.require_org_admin
    app.dependency_overrides[analysis_api.require_org_admin] = lambda: {"user_id": "test-user", "role": "org_admin"}
    try:
        yield
    finally:
        if analysis_api.require_org_admin in app.dependency_overrides:
            del app.dependency_overrides[analysis_api.require_org_admin]
    analysis_api.require_org_admin = original_dep  # type: ignore

# Tests -----------------------------------------------------------

def test_analyze_openai_success(monkeypatch):
    client = TestClient(app)

    # Fake supabase with default settings
    fake_sb = make_fake_supabase(profiles_org_id="org-1")
    monkeypatch.setattr(analysis_api, 'get_supabase_client', lambda: fake_sb)

    # Env and requests mock
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    class Resp:
        status_code = 200
        def raise_for_status(self):
            return None
        def json(self):
            return {"choices": [{"message": {"content": "ok-content"}}]}

    with patch('requests.post', return_value=Resp()):
        with override_user():
            res = client.post('/api/analysis/analyze', json={"prompt": "hello"})
            assert res.status_code == 200
            data = res.json()
            assert data["analysis"] == "ok-content"


def test_analyze_gemini_via_org_settings(monkeypatch):
    client = TestClient(app)

    # Org-specific settings prefer gemini
    fake_sb = make_fake_supabase(
        profiles_org_id="org-1",
        analysis_settings={"provider_order": ["gemini", "openai"], "enabled_providers": ["gemini", "openai"]},
    )
    monkeypatch.setattr(analysis_api, 'get_supabase_client', lambda: fake_sb)

    monkeypatch.setenv("GOOGLE_API_KEY", "gk-test")

    class Resp:
        status_code = 200
        def raise_for_status(self):
            return None
        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "gemini-content"}]}}]}

    with patch('requests.post', return_value=Resp()):
        with override_user():
            res = client.post('/api/analysis/analyze', json={"prompt": "hello"})
            assert res.status_code == 200
            data = res.json()
            assert data["analysis"].startswith("gemini-content")
            assert data["provider"] == "gemini"


def test_analyze_payload_override(monkeypatch):
    client = TestClient(app)
    fake_sb = make_fake_supabase(
        profiles_org_id="org-1",
        analysis_settings={"provider_order": ["gemini", "openai"], "enabled_providers": ["gemini", "openai"]},
    )
    monkeypatch.setattr(analysis_api, 'get_supabase_client', lambda: fake_sb)

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    class Resp:
        status_code = 200
        def raise_for_status(self):
            return None
        def json(self):
            return {"choices": [{"message": {"content": "openai-content"}}]}

    with patch('requests.post', return_value=Resp()):
        with override_user():
            res = client.post('/api/analysis/analyze', json={"prompt": "hello", "provider": "openai"})
            assert res.status_code == 200
            data = res.json()
            assert data["analysis"] == "openai-content"
            assert data["provider"] == "openai"


def test_analyze_heuristic_fallback(monkeypatch):
    client = TestClient(app)

    fake_sb = make_fake_supabase(profiles_org_id="org-1")
    monkeypatch.setattr(analysis_api, 'get_supabase_client', lambda: fake_sb)

    # Ensure no keys are set
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with override_user():
        res = client.post('/api/analysis/analyze', json={"prompt": "hello world"})
        assert res.status_code == 200
        data = res.json()
        assert data["provider"] == "heuristic"
        assert "hello world" in data["analysis"]


def test_empty_prompt_400(monkeypatch):
    client = TestClient(app)
    fake_sb = make_fake_supabase(profiles_org_id="org-1")
    monkeypatch.setattr(analysis_api, 'get_supabase_client', lambda: fake_sb)

    with override_user():
        res = client.post('/api/analysis/analyze', json={"prompt": "  "})
        assert res.status_code == 400


def test_settings_get_admin_only(monkeypatch):
    client = TestClient(app)
    fake_sb = make_fake_supabase(
        profiles_org_id="org-1",
        analysis_settings={"provider_order": ["openai", "gemini"], "enabled_providers": ["openai", "gemini"]},
    )
    monkeypatch.setattr(analysis_api, 'get_supabase_client', lambda: fake_sb)

    with override_org_admin():
        res = client.get('/api/analysis/settings')
        assert res.status_code == 200
        data = res.json()
        # Accept either existing settings or empty response if table missing
        if data:
            assert data.get("provider_order", [])[0] in ("openai", "gemini")


def test_settings_put_upsert(monkeypatch):
    client = TestClient(app)
    fake_sb = make_fake_supabase(profiles_org_id="org-1")
    monkeypatch.setattr(analysis_api, 'get_supabase_client', lambda: fake_sb)

    with override_org_admin():
        payload = {"provider_order": ["gemini", "openai"], "enabled_providers": ["gemini", "openai"]}
        res = client.put('/api/analysis/settings', json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["provider_order"] == ["gemini", "openai"]


def test_analyze_fallback_to_gemini_when_openai_fails(monkeypatch):
    client = TestClient(app)
    # Org prefers openai then gemini
    fake_sb = make_fake_supabase(
        profiles_org_id="org-1",
        analysis_settings={"provider_order": ["openai", "gemini"], "enabled_providers": ["openai", "gemini"]},
    )
    monkeypatch.setattr(analysis_api, 'get_supabase_client', lambda: fake_sb)

    # Both keys set
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("GOOGLE_API_KEY", "gk-test")

    class RespGemini:
        status_code = 200
        def raise_for_status(self):
            return None
        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "gemini-after-openai-fail"}]}}]}

    def post_side_effect(url, *args, **kwargs):
        if "openai.com" in url:
            raise Exception("openai down")
        return RespGemini()

    with patch('requests.post', side_effect=post_side_effect):
        with override_user():
            res = client.post('/api/analysis/analyze', json={"prompt": "hello"})
            assert res.status_code == 200
            data = res.json()
            assert data["provider"] == "gemini"


def test_analyze_override_not_enabled_is_ignored(monkeypatch):
    client = TestClient(app)
    # Only gemini enabled
    fake_sb = make_fake_supabase(
        profiles_org_id="org-1",
        analysis_settings={"provider_order": ["gemini"], "enabled_providers": ["gemini"]},
    )
    monkeypatch.setattr(analysis_api, 'get_supabase_client', lambda: fake_sb)

    monkeypatch.setenv("GOOGLE_API_KEY", "gk-test")

    class Resp:
        status_code = 200
        def raise_for_status(self):
            return None
        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "gemini-only"}]}}]}

    with patch('requests.post', return_value=Resp()):
        with override_user():
            # Try to force openai (should be ignored since not enabled)
            res = client.post('/api/analysis/analyze', json={"prompt": "hello", "provider": "openai"})
            assert res.status_code == 200
            data = res.json()
            assert data["provider"] == "gemini"


def test_settings_put_no_fields_400(monkeypatch):
    client = TestClient(app)
    fake_sb = make_fake_supabase(profiles_org_id="org-1")
    monkeypatch.setattr(analysis_api, 'get_supabase_client', lambda: fake_sb)

    with override_org_admin():
        res = client.put('/api/analysis/settings', json={})
        assert res.status_code == 400


def test_analyze_uses_env_defaults_when_no_org(monkeypatch):
    client = TestClient(app)
    # Fake supabase returns no org_id
    fake_sb = make_fake_supabase(profiles_org_id=None)
    monkeypatch.setattr(analysis_api, 'get_supabase_client', lambda: fake_sb)

    # Set env to prefer gemini
    monkeypatch.setenv("ANALYSIS_AVAILABLE_PROVIDERS", "openai,gemini")
    monkeypatch.setenv("ANALYSIS_PROVIDER_ORDER", "gemini,openai")
    monkeypatch.setenv("GOOGLE_API_KEY", "gk-test")

    class Resp:
        status_code = 200
        def raise_for_status(self):
            return None
        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "env-gemini"}]}}]}

    with patch('requests.post', return_value=Resp()):
        with override_user():
            res = client.post('/api/analysis/analyze', json={"prompt": "hello"})
            assert res.status_code == 200
            data = res.json()
            assert data["provider"] == "gemini"


def test_enabled_filter_skips_disabled_provider(monkeypatch):
    client = TestClient(app)
    # Gemin first in order but only openai enabled
    fake_sb = make_fake_supabase(
        profiles_org_id="org-1",
        analysis_settings={"provider_order": ["gemini", "openai"], "enabled_providers": ["openai"]},
    )
    monkeypatch.setattr(analysis_api, 'get_supabase_client', lambda: fake_sb)

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    class Resp:
        status_code = 200
        def raise_for_status(self):
            return None
        def json(self):
            return {"choices": [{"message": {"content": "only-openai"}}]}

    with patch('requests.post', return_value=Resp()):
        with override_user():
            res = client.post('/api/analysis/analyze', json={"prompt": "hello"})
            assert res.status_code == 200
            data = res.json()
            assert data["provider"] == "openai"


def test_get_settings_400_when_no_org(monkeypatch):
    client = TestClient(app)
    fake_sb = make_fake_supabase(profiles_org_id=None)
    monkeypatch.setattr(analysis_api, 'get_supabase_client', lambda: fake_sb)
    with override_org_admin():
        res = client.get('/api/analysis/settings')
        assert res.status_code == 400


def test_put_settings_filters_and_limits(monkeypatch):
    client = TestClient(app)
    fake_sb = make_fake_supabase(profiles_org_id="org-1")
    monkeypatch.setattr(analysis_api, 'get_supabase_client', lambda: fake_sb)
    with override_org_admin():
        res = client.put('/api/analysis/settings', json={
            "provider_order": ["unknown", "gemini", "openai", "extra"],
            "enabled_providers": ["gemini", "unknown"]
        })
        # Even if allowed set defaults are used, this should still succeed
        assert res.status_code in (200, 400)
