import types
import pytest

from middleware import permissions as perms
from middleware.permissions import (
    UserRole,
    get_user_role,
    get_user_organization_id,
    has_role,
    can_access_organization,
    can_access_rag_feature,
    PermissionChecker,
    validate_permissions,
    PermissionError,
    OrganizationAccessError,
    FeatureAccessError,
    require_role,
    require_org_access,
    require_feature_enabled,
    require_any_role,
)


class StubSupabase:
    def __init__(self, tables):
        self._tables = tables
        self._current_table = None
        self._filters = {}

    def from_(self, name):
        self._current_table = name
        self._filters = {}
        return self

    def select(self, *args, **kwargs):
        return self

    def eq(self, field, value):
        self._filters[field] = value
        return self

    def execute(self):
        rows = self._tables.get(self._current_table, [])

        def match(row):
            return all(row.get(k) == v for k, v in self._filters.items())

        data = [row for row in rows if match(row)]
        return types.SimpleNamespace(data=data)


@pytest.fixture
def supabase_parent():
    tables = {
        "organizations": [
            {"id": "child-org", "parent_organization_id": "parent-org"},
            {"id": "parent-org", "parent_organization_id": None},
        ]
    }
    return StubSupabase(tables)


@pytest.fixture
def supabase_features():
    tables = {
        "organization_rag_toggles": [
            {"organization_id": "org-1", "rag_feature": "enabled_feature", "enabled": True},
            {"organization_id": "org-1", "rag_feature": "disabled_feature", "enabled": False},
        ],
        "rag_feature_metadata": [
            {"rag_feature": "default_feature", "default_enabled": True},
        ],
    }
    return StubSupabase(tables)


def test_get_user_role_and_hierarchy():
    assert get_user_role({"role": "system_admin"}) is UserRole.SYSTEM_ADMIN
    assert get_user_role({"role": "unknown"}) is UserRole.USER
    assert get_user_role({}) is UserRole.USER

    salesperson = {"role": "salesperson"}
    assert has_role(salesperson, UserRole.USER)
    assert not has_role(salesperson, UserRole.MANAGER)


def test_get_user_organization_id():
    assert get_user_organization_id({"organization_id": "org-123"}) == "org-123"
    assert get_user_organization_id({}) is None


def test_can_access_organization_basic(supabase_parent):
    admin = {"role": "system_admin"}
    assert can_access_organization(admin, "any-org", supabase_parent)

    same_org_user = {"role": "user", "organization_id": "org-1"}
    assert can_access_organization(same_org_user, "org-1", supabase_parent)


def test_can_access_organization_parent_lookup(supabase_parent):
    parent_user = {"role": "org_admin", "organization_id": "parent-org"}
    assert can_access_organization(parent_user, "child-org", supabase_parent, check_parent=True)

    unrelated_user = {"role": "org_admin", "organization_id": "other-org"}
    assert not can_access_organization(unrelated_user, "child-org", supabase_parent, check_parent=True)


def test_can_access_rag_feature(supabase_features):
    sys_admin = {"role": "system_admin", "organization_id": "org-1"}
    assert can_access_rag_feature(sys_admin, "any", "org-2", supabase_features)

    user = {"role": "user", "organization_id": "org-1"}
    assert can_access_rag_feature(user, "enabled_feature", "org-1", supabase_features)
    assert not can_access_rag_feature(user, "disabled_feature", "org-1", supabase_features)
    assert can_access_rag_feature(user, "default_feature", "org-1", supabase_features)
    assert not can_access_rag_feature(user, "missing_feature", "org-1", supabase_features)
    assert not can_access_rag_feature(user, "enabled_feature", "other-org", supabase_features)


def test_can_access_rag_feature_handles_error(monkeypatch):
    class Boom:
        def from_(self, *_args, **_kwargs):
            raise RuntimeError("boom")
    user = {"role": "user", "organization_id": "org-1"}
    assert not can_access_rag_feature(user, "feature", "org-1", Boom())


def test_can_access_organization_error_path(monkeypatch):
    class Boom:
        def from_(self, *_args, **_kwargs):
            raise RuntimeError("boom")
    user = {"role": "org_admin", "organization_id": "org-1"}
    assert not can_access_organization(user, "child-org", Boom(), check_parent=True)


class StubRequest:
    def __init__(self, user):
        self.user = user


@pytest.fixture
def supabase_permissions(supabase_features):
    return supabase_features


def test_permission_checker_basic(supabase_permissions):
    org_admin = {"role": "org_admin", "organization_id": "org-1"}
    checker = PermissionChecker(org_admin, supabase_permissions)

    assert checker.can_manage_rag_features("org-1")
    assert not checker.can_manage_rag_features("org-2")
    assert checker.can_view_rag_features("org-1")
    assert checker.can_view_rag_features("org-2")
    assert checker.can_use_rag_feature("enabled_feature", "org-1")
    assert not checker.can_use_rag_feature("disabled_feature", "org-1")
    assert checker.get_accessible_organizations() == ["org-1"]

    sys_admin = {"role": "system_admin", "organization_id": "org-2"}
    checker_admin = PermissionChecker(sys_admin, supabase_permissions)
    assert checker_admin.can_manage_rag_features("org-9")
    assert checker_admin.get_accessible_organizations() == []


def test_permission_checker_error_logging(monkeypatch):
    class RaisingQuery:
        def select(self, *a, **k):
            return self

        def eq(self, *a, **k):
            return self

        def execute(self):
            raise RuntimeError("db down")

    class RaisingSupabase:
        def from_(self, *_args, **_kwargs):
            return RaisingQuery()

    checker = PermissionChecker({"role": "user", "organization_id": "org-1"}, RaisingSupabase())
    assert not checker.can_use_rag_feature("feature", "org-1")


def test_validate_permissions_with_stub(supabase_permissions):
    user = {"role": "org_admin", "organization_id": "org-1"}

    assert validate_permissions(user, "manage_rag_features", "org-1", supabase=supabase_permissions)
    assert not validate_permissions(user, "manage_rag_features", "org-2", supabase=supabase_permissions)
    assert validate_permissions(user, "use_rag_feature", "org-1", "default_feature", supabase_permissions)
    assert not validate_permissions(user, "use_rag_feature", "org-1", "missing", supabase_permissions)
    assert not validate_permissions(user, "use_rag_feature", "org-1", supabase=supabase_permissions)
    assert not validate_permissions(user, "unknown_action", "org-1", supabase=supabase_permissions)


@pytest.mark.asyncio
async def test_require_role_decorator():
    @require_role(UserRole.MANAGER)
    async def handler(user=None):
        return "ok"

    assert await handler(user={"role": "system_admin"}) == "ok"
    with pytest.raises(PermissionError):
        await handler(user={"role": "user"})


@pytest.mark.asyncio
async def test_require_org_access_decorator(monkeypatch):
    monkeypatch.setattr(perms, "can_access_organization", lambda user, org, check_parent=False: True)

    @require_org_access()
    async def handler(user=None, organization_id=None):
        return "ok"

    assert await handler(user={"role": "user"}, organization_id="org-1") == "ok"

    monkeypatch.setattr(perms, "can_access_organization", lambda *args, **kwargs: False)
    with pytest.raises(OrganizationAccessError):
        await handler(user={"role": "user"}, organization_id="org-1")


@pytest.mark.asyncio
async def test_require_feature_enabled_decorator(monkeypatch):
    monkeypatch.setattr(perms, "can_access_rag_feature", lambda *args, **kwargs: True)

    @require_feature_enabled("feature")
    async def handler(user=None, organization_id=None):
        return "ok"

    assert await handler(user={"role": "user", "organization_id": "org-1"}, organization_id="org-1") == "ok"

    monkeypatch.setattr(perms, "can_access_rag_feature", lambda *args, **kwargs: False)
    with pytest.raises(FeatureAccessError):
        await handler(user={"role": "user", "organization_id": "org-1"}, organization_id="org-1")


@pytest.mark.asyncio
async def test_require_any_role_decorator():
    @require_any_role([UserRole.MANAGER, UserRole.ORG_ADMIN])
    async def handler(user=None):
        return "ok"

    assert await handler(user={"role": "manager"}) == "ok"
    with pytest.raises(PermissionError):
        await handler(user={"role": "salesperson"})

