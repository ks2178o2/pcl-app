"""
Tests for validation middleware to push coverage above 80%.
Focus on exercising success and failure paths with lightweight stubs.
"""

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List
from unittest.mock import patch

import pytest

# Ensure project root (apps/app-api) is importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from middleware.validation import (  # noqa: E402
    RAGFeatureValidator,
    ValidationError,
    rag_validator,
    validate_bulk_toggle_operation,
    validate_feature_inheritance,
    validate_org_hierarchy,
    validate_rag_feature_enabled,
    validate_rag_feature_operation,
    validate_user_permissions,
)


class StubQuery:
    """Chainable Supabase style query helper."""

    def __init__(self, queue: List[List[Dict]]):
        self._queue = queue

    def select(self, *args, **kwargs):
        return self

    def eq(self, *args, **kwargs):
        return self

    def execute(self):
        data = self._queue.pop(0) if self._queue else []
        return SimpleNamespace(data=data)


class StubSupabase:
    """Minimal supabase client stub supporting .from_(table)."""

    def __init__(self, responses: Dict[str, List[List[Dict]]]):
        self._responses = {table: list(items) for table, items in responses.items()}
        self.from_calls: List[str] = []

    def from_(self, table: str):
        self.from_calls.append(table)
        queue = self._responses.setdefault(table, [])
        return StubQuery(queue)


@pytest.fixture
def validator():
    validator = RAGFeatureValidator()
    validator.supabase = StubSupabase({})
    return validator


def set_responses(target_validator: RAGFeatureValidator, responses: Dict[str, List[List[Dict]]]):
    stub = StubSupabase(responses)
    target_validator.supabase = stub
    return stub


@pytest.mark.asyncio
async def test_validate_rag_feature_exists_success(validator):
    set_responses(validator, {"rag_feature_metadata": [[{"rag_feature": "coach"}]]})
    assert await validator.validate_rag_feature_exists("coach") is True


@pytest.mark.asyncio
async def test_validate_rag_feature_exists_failure_logs(validator):
    stub = set_responses(validator, {})
    assert await validator.validate_rag_feature_exists("missing") is False
    assert stub.from_calls == ["rag_feature_metadata"]


@pytest.mark.asyncio
async def test_validate_rag_feature_exists_exception_path(validator):
    class Boom(StubSupabase):
        def from_(self, table: str):
            raise RuntimeError("boom")

    validator.supabase = Boom({})
    assert await validator.validate_rag_feature_exists("any") is False


@pytest.mark.asyncio
async def test_validate_rag_feature_enabled_success(validator):
    set_responses(
        validator,
        {
            "rag_feature_metadata": [[{"rag_feature": "summary"}]],
            "organization_rag_toggles": [[{"enabled": True}]],
        },
    )
    with patch.object(validator, "validate_rag_feature_exists", return_value=True):
        is_enabled, msg = await validator.validate_rag_feature_enabled("org-1", "summary")
        assert is_enabled is True
        assert msg == ""


@pytest.mark.asyncio
async def test_validate_rag_feature_enabled_disabled(validator):
    set_responses(
        validator,
        {
            "rag_feature_metadata": [[{"rag_feature": "summary"}]],
            "organization_rag_toggles": [[{"enabled": False}]],
        },
    )
    with patch.object(validator, "validate_rag_feature_exists", return_value=True):
        is_enabled, msg = await validator.validate_rag_feature_enabled("org-1", "summary")
        assert is_enabled is False
        assert "disabled" in msg


@pytest.mark.asyncio
async def test_validate_rag_feature_enabled_not_configured(validator):
    set_responses(
        validator,
        {
            "rag_feature_metadata": [[{"rag_feature": "summary"}]],
            "organization_rag_toggles": [[]],
        },
    )
    with patch.object(validator, "validate_rag_feature_exists", return_value=True):
        is_enabled, msg = await validator.validate_rag_feature_enabled("org-1", "summary")
        assert is_enabled is False
        assert "not configured" in msg


@pytest.mark.asyncio
async def test_validate_rag_feature_enabled_exception_path(validator):
    class Broken(StubSupabase):
        def from_(self, table: str):
            raise RuntimeError("bad toggle")

    validator.supabase = Broken({})
    with patch.object(validator, "validate_rag_feature_exists", return_value=True):
        ok, msg = await validator.validate_rag_feature_enabled("org", "feature")
        assert ok is False
        assert "Error validating RAG feature" in msg


@pytest.mark.asyncio
async def test_validate_rag_feature_enabled_missing_feature(validator):
    with patch.object(validator, "validate_rag_feature_exists", return_value=False):
        ok, msg = await validator.validate_rag_feature_enabled("org", "ghost")
        assert ok is False
        assert "does not exist" in msg


@pytest.mark.asyncio
async def test_validate_organization_exists_true(validator):
    set_responses(validator, {"organizations": [[{"id": "org-1"}]]})
    assert await validator.validate_organization_exists("org-1") is True


@pytest.mark.asyncio
async def test_validate_organization_exists_error(validator):
    class Broken(StubSupabase):
        def from_(self, table: str):
            raise RuntimeError("nope")

    validator.supabase = Broken({})
    assert await validator.validate_organization_exists("org-1") is False


@pytest.mark.asyncio
async def test_validate_org_hierarchy_circular_detected(validator):
    set_responses(
        validator,
        {
            "organizations": [[{"parent_organization_id": "child"}]],
        },
    )
    with patch.object(validator, "validate_organization_exists", return_value=True):
        valid, msg = await validator.validate_org_hierarchy("parent", "child")
        assert valid is False
        assert "Circular" in msg


@pytest.mark.asyncio
async def test_validate_org_hierarchy_self_reference(validator):
    with patch.object(validator, "validate_organization_exists", return_value=True):
        valid, msg = await validator.validate_org_hierarchy("org", "org")
        assert valid is False
        assert "own parent" in msg


@pytest.mark.asyncio
async def test_validate_org_hierarchy_parent_missing(validator):
    with patch.object(validator, "validate_organization_exists", side_effect=[False, True]):
        valid, msg = await validator.validate_org_hierarchy("parent", "child")
        assert valid is False
        assert "Parent organization" in msg


@pytest.mark.asyncio
async def test_validate_org_hierarchy_child_missing(validator):
    with patch.object(validator, "validate_organization_exists", side_effect=[True, False]):
        valid, msg = await validator.validate_org_hierarchy("parent", "child")
        assert valid is False
        assert "Child organization" in msg


@pytest.mark.asyncio
async def test_validate_org_hierarchy_exception_path(validator):
    class Explode(StubSupabase):
        def from_(self, table: str):
            raise RuntimeError("db down")

    validator.supabase = Explode({})
    with patch.object(validator, "validate_organization_exists", return_value=True):
        valid, msg = await validator.validate_org_hierarchy("p", "c")
        assert valid is False
        assert "Error validating hierarchy" in msg


@pytest.mark.asyncio
async def test_validate_feature_inheritance_parent_disabled(validator):
    set_responses(
        validator,
        {
            "organizations": [[{"parent_organization_id": "parent"}]],
            "organization_rag_toggles": [[{"enabled": False}]],
        },
    )
    can_enable, msg = await validator.validate_feature_inheritance("child", "summary")
    assert can_enable is False
    assert "disabled" in msg


@pytest.mark.asyncio
async def test_validate_feature_inheritance_no_parent_allows(validator):
    set_responses(
        validator,
        {"organizations": [[{"parent_organization_id": None}]]},
    )
    can_enable, msg = await validator.validate_feature_inheritance("child", "summary")
    assert can_enable is True
    assert msg == ""


@pytest.mark.asyncio
async def test_validate_feature_inheritance_parent_config_missing(validator):
    set_responses(
        validator,
        {
            "organizations": [[{"parent_organization_id": "parent"}]],
            "organization_rag_toggles": [[]],
        },
    )
    can_enable, msg = await validator.validate_feature_inheritance("child", "summary")
    assert can_enable is False
    assert "configured" in msg


@pytest.mark.asyncio
async def test_validate_feature_inheritance_org_missing(validator):
    set_responses(validator, {"organizations": [[]]})
    can_enable, msg = await validator.validate_feature_inheritance("missing", "summary")
    assert can_enable is False
    assert "not found" in msg


@pytest.mark.asyncio
async def test_validate_feature_inheritance_exception(validator):
    class Explode(StubSupabase):
        def from_(self, table: str):
            raise RuntimeError("kaput")

    validator.supabase = Explode({})
    can_enable, msg = await validator.validate_feature_inheritance("org", "feat")
    assert can_enable is False
    assert "Error validating inheritance" in msg


@pytest.mark.asyncio
async def test_validate_feature_inheritance_parent_enabled_success(validator):
    set_responses(
        validator,
        {
            "organizations": [[{"parent_organization_id": "parent"}]],
            "organization_rag_toggles": [[{"enabled": True}]],
        },
    )
    can_enable, msg = await validator.validate_feature_inheritance("child", "summary")
    assert can_enable is True
    assert msg == ""


@pytest.mark.asyncio
async def test_validate_user_can_manage_features_denied(validator):
    with patch("middleware.validation.PermissionChecker") as mock_checker:
        instance = mock_checker.return_value
        instance.can_manage_rag_features.return_value = False
        instance.user_role.value = "viewer"
        allowed, msg = await validator.validate_user_can_manage_features({"id": "u1"}, "org-1")
        assert allowed is False
        assert "viewer" in msg


@pytest.mark.asyncio
async def test_validate_user_can_manage_features_exception(validator):
    with patch("middleware.validation.PermissionChecker", side_effect=RuntimeError("boom")):
        allowed, msg = await validator.validate_user_can_manage_features({"id": "u1"}, "org-1")
        assert allowed is False
        assert "Error validating permissions" in msg


@pytest.mark.asyncio
async def test_validate_user_can_manage_features_success(validator):
    with patch("middleware.validation.PermissionChecker") as mock_checker:
        instance = mock_checker.return_value
        instance.can_manage_rag_features.return_value = True
        result = await validator.validate_user_can_manage_features({"id": "u1"}, "org-1")
        assert result == (True, "")


@pytest.mark.asyncio
async def test_validate_rag_feature_operation_missing_org():
    with patch.object(rag_validator, "validate_organization_exists", return_value=False):
        result = await validate_rag_feature_operation("org-x", "feature", "use")
        assert result == {"success": False, "error": "Organization org-x does not exist"}


@pytest.mark.asyncio
async def test_validate_rag_feature_operation_enabled_path():
    with patch.object(rag_validator, "validate_organization_exists", return_value=True):
        with patch.object(rag_validator, "validate_rag_feature_exists", return_value=True):
            with patch.object(rag_validator, "validate_rag_feature_enabled", return_value=(True, "")):
                result = await validate_rag_feature_operation("org-1", "feature", "upload")
                assert result["success"] is True


@pytest.mark.asyncio
async def test_validate_rag_feature_operation_feature_missing():
    with patch.object(rag_validator, "validate_organization_exists", return_value=True):
        with patch.object(rag_validator, "validate_rag_feature_exists", return_value=False):
            result = await validate_rag_feature_operation("org-1", "unknown", "use")
            assert result["success"] is False
            assert "does not exist" in result["error"]


@pytest.mark.asyncio
async def test_validate_rag_feature_operation_validation_exception():
    with patch.object(rag_validator, "validate_organization_exists", side_effect=RuntimeError("boom")):
        result = await validate_rag_feature_operation("org-1", "feature", "use")
        assert result["success"] is False
        assert "Validation error" in result["error"]


@pytest.mark.asyncio
async def test_validate_rag_feature_operation_not_enabled():
    with patch.object(rag_validator, "validate_organization_exists", return_value=True):
        with patch.object(rag_validator, "validate_rag_feature_exists", return_value=True):
            with patch.object(rag_validator, "validate_rag_feature_enabled", return_value=(False, "blocked")):
                result = await validate_rag_feature_operation("org", "feature", "use")
                assert result == {"success": False, "error": "blocked"}


@pytest.mark.asyncio
async def test_validate_rag_feature_operation_configuration_skip():
    with patch.object(rag_validator, "validate_organization_exists", return_value=True):
        with patch.object(rag_validator, "validate_rag_feature_exists", return_value=True):
            result = await validate_rag_feature_operation("org", "feature", "configure")
            assert result == {"success": True, "error": None}


@pytest.mark.asyncio
async def test_validate_bulk_toggle_operation_invalid_collection():
    updates = {"missing": True, "ok": True}
    user = {"id": "u1"}
    with patch.object(rag_validator, "validate_organization_exists", return_value=True):
        with patch.object(rag_validator, "validate_user_can_manage_features", return_value=(True, "")):
            with patch.object(
                rag_validator,
                "validate_rag_feature_exists",
                side_effect=lambda name: name == "ok",
            ):
                result = await validate_bulk_toggle_operation("org-1", updates, user)
                assert result["success"] is False
                assert "missing" in result["error"]


@pytest.mark.asyncio
async def test_validate_bulk_toggle_operation_org_missing():
    with patch.object(rag_validator, "validate_organization_exists", return_value=False):
        result = await validate_bulk_toggle_operation("org", {"feature": True}, {"id": "u1"})
        assert result["success"] is False
        assert "does not exist" in result["error"]


@pytest.mark.asyncio
async def test_validate_bulk_toggle_operation_inheritance_error():
    with patch.object(rag_validator, "validate_organization_exists", return_value=True):
        with patch.object(rag_validator, "validate_user_can_manage_features", return_value=(True, "")):
            with patch.object(rag_validator, "validate_rag_feature_exists", return_value=True):
                with patch.object(
                    rag_validator,
                    "validate_feature_inheritance",
                    return_value=(False, "blocked"),
                ):
                    result = await validate_bulk_toggle_operation("org", {"feat": True}, {"id": "u1"})
                    assert result["success"] is False
                    assert "blocked" in result["error"]


@pytest.mark.asyncio
async def test_validate_bulk_toggle_operation_exception():
    with patch.object(rag_validator, "validate_organization_exists", side_effect=RuntimeError("boom")):
        result = await validate_bulk_toggle_operation("org", {"feat": True}, {"id": "u1"})
        assert result["success"] is False
        assert "Validation error" in result["error"]


@pytest.mark.asyncio
async def test_validate_bulk_toggle_operation_permission_failure():
    updates = {"feature": True}
    user = {"id": "u1"}
    with patch.object(rag_validator, "validate_organization_exists", return_value=True):
        with patch.object(
            rag_validator,
            "validate_user_can_manage_features",
            return_value=(False, "nope"),
        ):
            result = await validate_bulk_toggle_operation("org-1", updates, user)
            assert result == {"success": False, "error": "nope"}


@pytest.mark.asyncio
async def test_validate_bulk_toggle_operation_success():
    updates = {"feature": True}
    user = {"id": "u1"}
    with patch.object(rag_validator, "validate_organization_exists", return_value=True):
        with patch.object(rag_validator, "validate_user_can_manage_features", return_value=(True, "")):
            with patch.object(rag_validator, "validate_rag_feature_exists", return_value=True):
                with patch.object(
                    rag_validator,
                    "validate_feature_inheritance",
                    return_value=(True, ""),
                ):
                    result = await validate_bulk_toggle_operation("org-1", updates, user)
                    assert result == {"success": True, "error": None}


@pytest.mark.asyncio
async def test_validate_decorator_missing_args_raises():
    @validate_rag_feature_enabled()
    async def fn(feature_name=None, organization_id=None):
        return True

    with pytest.raises(ValidationError):
        await fn()


@pytest.mark.asyncio
async def test_validate_org_hierarchy_decorator_uses_validator():
    @validate_org_hierarchy()
    async def fn(parent_id=None, child_id=None):
        return "ok"

    with patch.object(rag_validator, "validate_org_hierarchy", return_value=(True, "")):
        assert await fn(parent_id="p", child_id="c") == "ok"


@pytest.mark.asyncio
async def test_validate_user_permissions_decorator_blocks():
    @validate_user_permissions()
    async def fn(user=None, organization_id=None):
        return "ok"

    with patch.object(
        rag_validator,
        "validate_user_can_manage_features",
        return_value=(False, "denied"),
    ):
        with pytest.raises(ValidationError):
            await fn(user={"id": "u1"}, organization_id="org-1")


@pytest.mark.asyncio
async def test_validate_user_permissions_decorator_missing_params():
    @validate_user_permissions()
    async def fn(user=None, organization_id=None):
        return "ok"

    with pytest.raises(ValidationError):
        await fn(user=None, organization_id="org-1")


@pytest.mark.asyncio
async def test_validate_feature_inheritance_decorator_success():
    @validate_feature_inheritance()
    async def fn(feature_name=None, organization_id=None):
        return "done"

    with patch.object(rag_validator, "validate_feature_inheritance", return_value=(True, "")):
        assert await fn(feature_name="feature", organization_id="org") == "done"


@pytest.mark.asyncio
async def test_validate_user_permissions_decorator_success():
    @validate_user_permissions()
    async def fn(user=None, organization_id=None):
        return "done"

    with patch.object(rag_validator, "validate_user_can_manage_features", return_value=(True, "")):
        assert await fn(user={"id": "u"}, organization_id="org") == "done"


@pytest.mark.asyncio
async def test_validate_rag_feature_enabled_decorator_success():
    @validate_rag_feature_enabled()
    async def fn(feature_name=None, organization_id=None):
        return "done"

    with patch.object(rag_validator, "validate_rag_feature_enabled", return_value=(True, "")):
        assert await fn(feature_name="feat", organization_id="org") == "done"


