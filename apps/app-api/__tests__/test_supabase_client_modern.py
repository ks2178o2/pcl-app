import types
import pytest

from services.supabase_client import SupabaseClientManager, get_supabase_client


@pytest.fixture(autouse=True)
def reset_manager():
    SupabaseClientManager._instance = None
    SupabaseClientManager._client = None
    yield
    SupabaseClientManager._instance = None
    SupabaseClientManager._client = None


def test_get_client_returns_none_without_key(monkeypatch):
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_KEY", raising=False)
    manager = SupabaseClientManager()
    assert manager.get_client() is None


def test_get_client_initializes_once(monkeypatch):
    fake_client = object()

    def fake_create(url, key):
        assert url == "https://example.supabase.co"
        assert key == "test-key"
        return fake_client

    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")
    monkeypatch.setattr("services.supabase_client.create_client", fake_create)

    manager = SupabaseClientManager()
    assert manager.get_client() is fake_client
    # Cached instance
    assert manager.get_client() is fake_client


def test_get_client_handles_exception(monkeypatch):
    def fake_create(url, key):
        raise RuntimeError("boom")

    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")
    monkeypatch.setattr("services.supabase_client.create_client", fake_create)

    manager = SupabaseClientManager()
    assert manager.get_client() is None


@pytest.mark.asyncio
async def test_health_check_success(monkeypatch):
    class FakeQuery:
        def select(self, *_):
            return self

        def limit(self, *_):
            return self

        def execute(self):
            return types.SimpleNamespace(data=[{"id": "123"}])

    class FakeClient:
        def from_(self, *_):
            return FakeQuery()

    manager = SupabaseClientManager()
    manager._client = FakeClient()

    result = await manager.health_check()
    assert result == {"success": True, "status": "healthy", "response_time": 50.5}


@pytest.mark.asyncio
async def test_health_check_failure(monkeypatch):
    class BadClient:
        def from_(self, *_):
            raise RuntimeError("db down")

    manager = SupabaseClientManager()
    manager._client = BadClient()

    result = await manager.health_check()
    assert result["success"] is False
    assert result["status"] == "unhealthy"
    assert "db down" in result["error"]


class StubQuery:
    def __init__(self, data=None):
        self.data = data or []
        self.filters = []
        self.payload = None

    # Shared chainable methods
    def select(self, *_):
        return self

    def insert(self, data):
        self.payload = data
        self.data = [data]
        return self

    def update(self, data):
        self.payload = data
        self.data = [data]
        return self

    def delete(self):
        return self

    def eq(self, key, value):
        self.filters.append((key, value))
        return self

    def execute(self):
        return types.SimpleNamespace(data=self.data)


class StubSupabase:
    def __init__(self, tables=None):
        self.tables = tables or {}
        self.last_table = None

    def from_(self, table):
        self.last_table = table
        return self.tables.setdefault(table, StubQuery())


@pytest.mark.asyncio
async def test_execute_query_success():
    tables = {"profiles": StubQuery([{"id": "user-1"}])}
    manager = SupabaseClientManager()
    manager._client = StubSupabase(tables)

    result = await manager.execute_query("profiles", filters={"id": "user-1"})
    assert result["success"] is True
    assert result["data"] == [{"id": "user-1"}]


@pytest.mark.asyncio
async def test_execute_query_failure():
    class BadClient:
        def from_(self, *_):
            raise RuntimeError("boom")

    manager = SupabaseClientManager()
    manager._client = BadClient()

    result = await manager.execute_query("profiles")
    assert result["success"] is False
    assert "boom" in result["error"]


@pytest.mark.asyncio
async def test_insert_update_delete(monkeypatch):
    tables = {"profiles": StubQuery()}
    manager = SupabaseClientManager()
    manager._client = StubSupabase(tables)

    insert_result = await manager.insert_data("profiles", {"id": "user-1"})
    assert insert_result["success"] is True
    assert insert_result["data"] == [{"id": "user-1"}]

    update_result = await manager.update_data("profiles", {"name": "Alice"}, {"id": "user-1"})
    assert update_result["success"] is True
    assert update_result["data"] == [{"name": "Alice"}]

    tables["profiles"].data = [{"id": "user-1"}]
    delete_result = await manager.delete_data("profiles", {"id": "user-1"})
    assert delete_result["success"] is True
    assert delete_result["deleted_count"] == 1


@pytest.mark.asyncio
async def test_insert_handles_exception():
    class BadClient:
        def from_(self, *_):
            raise RuntimeError("boom")

    manager = SupabaseClientManager()
    manager._client = BadClient()

    result = await manager.insert_data("profiles", {"id": "user-1"})
    assert result["success"] is False
    assert "boom" in result["error"]


def test_get_supabase_client_helper(monkeypatch):
    fake_client = object()
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "key")
    monkeypatch.setattr("services.supabase_client.create_client", lambda *a, **k: fake_client)
    client = get_supabase_client()
    assert client is fake_client

