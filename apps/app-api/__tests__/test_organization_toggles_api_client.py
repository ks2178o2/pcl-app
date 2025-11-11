import pytest
from unittest.mock import Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestOrganizationTogglesAPIClient:
    def _build_app_with_mocks(self, toggles_response=None, overrides=None):
        import importlib
        import middleware.permissions as perms
        # Monkeypatch admin decorators to no-ops for tests
        original_admin = getattr(perms, 'require_admin_access', None)
        original_org_admin = getattr(perms, 'require_org_admin', None)
        perms.require_admin_access = lambda f: f
        perms.require_org_admin = lambda f: f
        try:
            import api.organization_toggles_api as mod
            mod = importlib.reload(mod)
        finally:
            if original_admin is not None:
                perms.require_admin_access = original_admin
            if original_org_admin is not None:
                perms.require_org_admin = original_org_admin

        app = FastAPI()
        app.include_router(mod.router)

        # Default mock tenant service
        class DummyTenantService:
            async def get_rag_feature_toggles(self, org_id):
                return toggles_response or {
                    'success': True,
                    'toggles': [
                        {'organization_id': org_id, 'rag_feature': 'f1', 'enabled': True, 'category': 'sales', 'is_inherited': False},
                        {'organization_id': org_id, 'rag_feature': 'f2', 'enabled': False, 'category': 'admin', 'is_inherited': True, 'inherited_from': 'parent-1'},
                    ]
                }
            async def update_rag_feature_toggle(self, organization_id, rag_feature, enabled):
                return {'success': True, 'toggle': {'organization_id': organization_id, 'rag_feature': rag_feature, 'enabled': enabled, 'category': 'sales', 'is_inherited': False}}
            async def bulk_update_rag_toggles(self, organization_id, toggle_updates):
                updated = [{'organization_id': organization_id, 'rag_feature': k, 'enabled': v, 'category': 'sales', 'is_inherited': False} for k, v in toggle_updates.items()]
                return {'success': True, 'updated_toggles': updated}

        # Dependency overrides
        app.dependency_overrides[mod.get_tenant_isolation_service] = lambda: (overrides.get('tenant_service') if overrides and overrides.get('tenant_service') else DummyTenantService())
        app.dependency_overrides[mod.get_current_user] = lambda: (overrides.get('user') if overrides and overrides.get('user') else {"id": "user-1", "role": "org_admin", "organization_id": "org-123"})
        # Ensure supabase dependency (only used on list) is harmless
        app.dependency_overrides[mod.get_supabase] = lambda: Mock()

        # Lightweight PermissionChecker replacement
        class DummyChecker:
            def __init__(self, user):
                self.user = user
                self._can_manage = overrides.get('can_manage', True) if overrides else True
                self._can_view = overrides.get('can_view', True) if overrides else True
            def can_manage_rag_features(self, *_a, **_k):
                return self._can_manage
            def can_view_rag_features(self, *_a, **_k):
                return self._can_view
        mod.PermissionChecker = DummyChecker
        return app, mod

    def test_list_toggles_success(self):
        app, _ = self._build_app_with_mocks()
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles')
            assert r.status_code == 200
            body = r.json()
            assert body['success'] is True
            assert body['total'] == 2
            assert len(body['data']) == 2

    def test_list_toggles_filters_and_enabled_only(self):
        app, _ = self._build_app_with_mocks()
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles?category=sales&enabled_only=true')
            assert r.status_code == 200
            body = r.json()
            assert body['total'] == 1
            assert body['data'][0]['rag_feature'] == 'f1'

    def test_list_toggles_permission_denied(self):
        app, _ = self._build_app_with_mocks(overrides={'can_manage': False})
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles')
            assert r.status_code == 403

    def test_list_toggles_service_error(self):
        bad = {'success': False, 'error': 'svc fail'}
        app, _ = self._build_app_with_mocks(toggles_response=bad)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles')
            assert r.status_code == 500

    def test_get_toggle_success(self):
        app, _ = self._build_app_with_mocks()
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/f1')
            assert r.status_code == 200
            assert r.json()['data']['rag_feature'] == 'f1'

    def test_get_toggle_not_found(self):
        resp = {'success': True, 'toggles': []}
        app, _ = self._build_app_with_mocks(toggles_response=resp)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/missing')
            assert r.status_code == 404

    def test_get_toggle_permission_denied(self):
        app, _ = self._build_app_with_mocks(overrides={'can_manage': False})
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/f1')
            assert r.status_code == 403

    def test_get_toggle_service_error(self):
        bad = {'success': False}
        app, _ = self._build_app_with_mocks(toggles_response=bad)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/f1')
            assert r.status_code == 500

    def test_update_toggle_success(self):
        app, _ = self._build_app_with_mocks()
        with TestClient(app) as c:
            r = c.patch('/api/v1/orgs/org-123/rag-toggles/f1', json={'enabled': False})
            assert r.status_code == 200
            assert r.json()['data']['enabled'] is False

    def test_update_toggle_permission_denied(self):
        app, _ = self._build_app_with_mocks(overrides={'can_manage': False})
        with TestClient(app) as c:
            r = c.patch('/api/v1/orgs/org-123/rag-toggles/f1', json={'enabled': True})
            assert r.status_code == 403

    def test_update_toggle_service_error(self):
        class BadService:
            async def get_rag_feature_toggles(self, org_id):
                return {'success': True, 'toggles': []}
            async def update_rag_feature_toggle(self, organization_id, rag_feature, enabled):
                return {'success': False, 'error': 'fail'}
        app, mod = self._build_app_with_mocks(overrides={'tenant_service': BadService()})
        with TestClient(app) as c:
            r = c.patch('/api/v1/orgs/org-123/rag-toggles/f1', json={'enabled': True})
            assert r.status_code == 500

    def test_bulk_update_success(self):
        app, _ = self._build_app_with_mocks()
        with TestClient(app) as c:
            r = c.post('/api/v1/orgs/org-123/rag-toggles/bulk', json={'updates': {'f1': True, 'f3': False}})
            assert r.status_code == 200
            assert r.json()['total'] == 2

    def test_bulk_update_permission_denied(self):
        app, _ = self._build_app_with_mocks(overrides={'can_manage': False})
        with TestClient(app) as c:
            r = c.post('/api/v1/orgs/org-123/rag-toggles/bulk', json={'updates': {'f1': True}})
            assert r.status_code == 403

    def test_bulk_update_service_error(self):
        class BadService:
            async def get_rag_feature_toggles(self, org_id):
                return {'success': True, 'toggles': []}
            async def bulk_update_rag_toggles(self, organization_id, toggle_updates):
                return {'success': False}
        app, _ = self._build_app_with_mocks(overrides={'tenant_service': BadService()})
        with TestClient(app) as c:
            r = c.post('/api/v1/orgs/org-123/rag-toggles/bulk', json={'updates': {'f1': True}})
            assert r.status_code == 500

    def test_enabled_features_success(self):
        # Minimal app mounting only enabled handler
        import api.organization_toggles_api as mod
        app = FastAPI()
        class DummyService:
            async def get_rag_feature_toggles(self, org_id):
                return {
                    'success': True,
                    'toggles': [
                        {'organization_id': org_id, 'rag_feature': 'f1', 'enabled': True, 'category': 'sales'},
                        {'organization_id': org_id, 'rag_feature': 'f2', 'enabled': False, 'category': 'admin'},
                    ]
                }
        app.dependency_overrides[mod.get_tenant_isolation_service] = lambda: DummyService()
        app.dependency_overrides[mod.get_current_user] = lambda: {"id": "user-1", "role": "org_admin", "organization_id": "org-123"}
        class DummyChecker:
            def __init__(self, *_a, **_k): pass
            def can_view_rag_features(self, *_a, **_k): return True
        mod.PermissionChecker = DummyChecker
        app.get('/api/v1/orgs/{org_id}/rag-toggles/enabled')(mod.get_enabled_rag_features)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/enabled')
            assert r.status_code == 200

    def test_enabled_features_permission_denied(self):
        import api.organization_toggles_api as mod
        app = FastAPI()
        class DummyService:
            async def get_rag_feature_toggles(self, org_id):
                return {'success': True, 'toggles': []}
        app.dependency_overrides[mod.get_tenant_isolation_service] = lambda: DummyService()
        app.dependency_overrides[mod.get_current_user] = lambda: {"id": "user-1", "role": "org_admin", "organization_id": "org-123"}
        class DummyChecker:
            def __init__(self, *_a, **_k): pass
            def can_view_rag_features(self, *_a, **_k): return False
        mod.PermissionChecker = DummyChecker
        app.get('/api/v1/orgs/{org_id}/rag-toggles/enabled')(mod.get_enabled_rag_features)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/enabled')
            assert r.status_code == 403

    def test_inherited_features_success(self):
        import api.organization_toggles_api as mod
        app = FastAPI()
        class DummyService:
            async def get_rag_feature_toggles(self, org_id):
                return {
                    'success': True,
                    'toggles': [
                        {'organization_id': org_id, 'rag_feature': 'f1', 'enabled': True, 'category': 'sales', 'is_inherited': True},
                        {'organization_id': org_id, 'rag_feature': 'f2', 'enabled': False, 'category': 'admin', 'is_inherited': False},
                    ]
                }
        app.dependency_overrides[mod.get_tenant_isolation_service] = lambda: DummyService()
        app.dependency_overrides[mod.get_current_user] = lambda: {"id": "user-1", "role": "org_admin", "organization_id": "org-123"}
        class DummyChecker:
            def __init__(self, *_a, **_k): pass
            def can_view_rag_features(self, *_a, **_k): return True
        mod.PermissionChecker = DummyChecker
        app.get('/api/v1/orgs/{org_id}/rag-toggles/inherited')(mod.get_inherited_rag_features)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/inherited')
            assert r.status_code == 200

    def test_inherited_features_permission_denied(self):
        import api.organization_toggles_api as mod
        app = FastAPI()
        class DummyService:
            async def get_rag_feature_toggles(self, org_id):
                return {'success': True, 'toggles': []}
        app.dependency_overrides[mod.get_tenant_isolation_service] = lambda: DummyService()
        app.dependency_overrides[mod.get_current_user] = lambda: {"id": "user-1", "role": "org_admin", "organization_id": "org-123"}
        class DummyChecker:
            def __init__(self, *_a, **_k): pass
            def can_view_rag_features(self, *_a, **_k): return False
        mod.PermissionChecker = DummyChecker
        app.get('/api/v1/orgs/{org_id}/rag-toggles/inherited')(mod.get_inherited_rag_features)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/inherited')
            assert r.status_code == 403

    def test_summary_success(self):
        import api.organization_toggles_api as mod
        app = FastAPI()
        class DummyService:
            async def get_rag_feature_toggles(self, org_id):
                return {
                    'success': True,
                    'toggles': [
                        {'organization_id': org_id, 'rag_feature': 'f1', 'enabled': True, 'category': 'sales', 'is_inherited': True},
                        {'organization_id': org_id, 'rag_feature': 'f2', 'enabled': False, 'category': 'admin', 'is_inherited': False},
                    ]
                }
        app.dependency_overrides[mod.get_tenant_isolation_service] = lambda: DummyService()
        app.dependency_overrides[mod.get_current_user] = lambda: {"id": "user-1", "role": "org_admin", "organization_id": "org-123"}
        class DummyChecker:
            def __init__(self, *_a, **_k): pass
            def can_view_rag_features(self, *_a, **_k): return True
        mod.PermissionChecker = DummyChecker
        app.get('/api/v1/orgs/{org_id}/rag-toggles/summary')(mod.get_rag_toggle_summary)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/summary')
            assert r.status_code == 200

    def test_summary_permission_denied(self):
        import api.organization_toggles_api as mod
        app = FastAPI()
        class DummyService:
            async def get_rag_feature_toggles(self, org_id):
                return {'success': True, 'toggles': []}
        app.dependency_overrides[mod.get_tenant_isolation_service] = lambda: DummyService()
        app.dependency_overrides[mod.get_current_user] = lambda: {"id": "user-1", "role": "org_admin", "organization_id": "org-123"}
        class DummyChecker:
            def __init__(self, *_a, **_k): pass
            def can_view_rag_features(self, *_a, **_k): return False
        mod.PermissionChecker = DummyChecker
        app.get('/api/v1/orgs/{org_id}/rag-toggles/summary')(mod.get_rag_toggle_summary)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/summary')
            assert r.status_code == 403

    def test_enabled_features_with_category_filter(self):
        import api.organization_toggles_api as mod
        app = FastAPI()
        class DummyService:
            async def get_rag_feature_toggles(self, org_id):
                return {
                    'success': True,
                    'toggles': [
                        {'organization_id': org_id, 'rag_feature': 'f1', 'enabled': True, 'category': 'sales'},
                        {'organization_id': org_id, 'rag_feature': 'f2', 'enabled': True, 'category': 'admin'},
                    ]
                }
        app.dependency_overrides[mod.get_tenant_isolation_service] = lambda: DummyService()
        app.dependency_overrides[mod.get_current_user] = lambda: {"id": "user-1", "role": "org_admin", "organization_id": "org-123"}
        class DummyChecker:
            def __init__(self, *_a, **_k): pass
            def can_view_rag_features(self, *_a, **_k): return True
        mod.PermissionChecker = DummyChecker
        app.get('/api/v1/orgs/{org_id}/rag-toggles/enabled')(mod.get_enabled_rag_features)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/enabled?category=sales')
            assert r.status_code == 200
            assert 'f1' in r.json()['data']
            assert 'f2' not in r.json()['data']

    def test_enabled_features_service_error(self):
        import api.organization_toggles_api as mod
        app = FastAPI()
        class BadService:
            async def get_rag_feature_toggles(self, org_id):
                return {'success': False}
        app.dependency_overrides[mod.get_tenant_isolation_service] = lambda: BadService()
        app.dependency_overrides[mod.get_current_user] = lambda: {"id": "user-1", "role": "org_admin", "organization_id": "org-123"}
        class DummyChecker:
            def __init__(self, *_a, **_k): pass
            def can_view_rag_features(self, *_a, **_k): return True
        mod.PermissionChecker = DummyChecker
        app.get('/api/v1/orgs/{org_id}/rag-toggles/enabled')(mod.get_enabled_rag_features)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/enabled')
            assert r.status_code == 500

    def test_inherited_features_service_error(self):
        import api.organization_toggles_api as mod
        app = FastAPI()
        class BadService:
            async def get_rag_feature_toggles(self, org_id):
                return {'success': False}
        app.dependency_overrides[mod.get_tenant_isolation_service] = lambda: BadService()
        app.dependency_overrides[mod.get_current_user] = lambda: {"id": "user-1", "role": "org_admin", "organization_id": "org-123"}
        class DummyChecker:
            def __init__(self, *_a, **_k): pass
            def can_view_rag_features(self, *_a, **_k): return True
        mod.PermissionChecker = DummyChecker
        app.get('/api/v1/orgs/{org_id}/rag-toggles/inherited')(mod.get_inherited_rag_features)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/inherited')
            assert r.status_code == 500

    def test_summary_zero_toggles(self):
        import api.organization_toggles_api as mod
        app = FastAPI()
        class DummyService:
            async def get_rag_feature_toggles(self, org_id):
                return {'success': True, 'toggles': []}
        app.dependency_overrides[mod.get_tenant_isolation_service] = lambda: DummyService()
        app.dependency_overrides[mod.get_current_user] = lambda: {"id": "user-1", "role": "org_admin", "organization_id": "org-123"}
        class DummyChecker:
            def __init__(self, *_a, **_k): pass
            def can_view_rag_features(self, *_a, **_k): return True
        mod.PermissionChecker = DummyChecker
        app.get('/api/v1/orgs/{org_id}/rag-toggles/summary')(mod.get_rag_toggle_summary)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/summary')
            assert r.status_code == 200
            data = r.json()['data']
            assert data['enabled_percentage'] == 0.0

    def test_summary_service_error(self):
        import api.organization_toggles_api as mod
        app = FastAPI()
        class BadService:
            async def get_rag_feature_toggles(self, org_id):
                return {'success': False}
        app.dependency_overrides[mod.get_tenant_isolation_service] = lambda: BadService()
        app.dependency_overrides[mod.get_current_user] = lambda: {"id": "user-1", "role": "org_admin", "organization_id": "org-123"}
        class DummyChecker:
            def __init__(self, *_a, **_k): pass
            def can_view_rag_features(self, *_a, **_k): return True
        mod.PermissionChecker = DummyChecker
        app.get('/api/v1/orgs/{org_id}/rag-toggles/summary')(mod.get_rag_toggle_summary)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/summary')
            assert r.status_code == 500
    
    def test_exception_paths_list_toggles(self):
        app, _ = self._build_app_with_mocks()
        class ServiceThatRaises:
            async def get_rag_feature_toggles(self, org_id):
                raise Exception("Service exception")
        app, mod = self._build_app_with_mocks(overrides={'tenant_service': ServiceThatRaises()})
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles')
            assert r.status_code == 500
    
    def test_exception_paths_get_toggle(self):
        app, _ = self._build_app_with_mocks()
        class ServiceThatRaises:
            async def get_rag_feature_toggles(self, org_id):
                raise Exception("Service exception")
        app, mod = self._build_app_with_mocks(overrides={'tenant_service': ServiceThatRaises()})
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/f1')
            assert r.status_code == 500
    
    def test_exception_paths_update_toggle(self):
        app, _ = self._build_app_with_mocks()
        class ServiceThatRaises:
            async def get_rag_feature_toggles(self, org_id):
                return {'success': True, 'toggles': [{'rag_feature': 'f1'}]}
            async def update_rag_feature_toggle(self, org_id, feature, enabled):
                raise Exception("Update exception")
        app, mod = self._build_app_with_mocks(overrides={'tenant_service': ServiceThatRaises()})
        with TestClient(app) as c:
            r = c.patch('/api/v1/orgs/org-123/rag-toggles/f1', json={'enabled': True})
            assert r.status_code == 500
    
    def test_exception_paths_bulk_update(self):
        app, _ = self._build_app_with_mocks()
        class ServiceThatRaises:
            async def get_rag_feature_toggles(self, org_id):
                return {'success': True, 'toggles': []}
            async def bulk_update_rag_toggles(self, org_id, updates):
                raise Exception("Bulk exception")
        app, mod = self._build_app_with_mocks(overrides={'tenant_service': ServiceThatRaises()})
        with TestClient(app) as c:
            r = c.post('/api/v1/orgs/org-123/rag-toggles/bulk', json={'updates': {'f1': True}})
            assert r.status_code == 500
    
    def test_exception_paths_enabled_features(self):
        import api.organization_toggles_api as mod
        app = FastAPI()
        class ServiceThatRaises:
            async def get_rag_feature_toggles(self, org_id):
                raise Exception("Enabled features exception")
        app.dependency_overrides[mod.get_tenant_isolation_service] = lambda: ServiceThatRaises()
        app.dependency_overrides[mod.get_current_user] = lambda: {"id": "user-1", "role": "org_admin"}
        class DummyChecker:
            def __init__(self, *_a, **_k): pass
            def can_view_rag_features(self, *_a, **_k): return True
        mod.PermissionChecker = DummyChecker
        app.get('/api/v1/orgs/{org_id}/rag-toggles/enabled')(mod.get_enabled_rag_features)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/enabled')
            assert r.status_code == 500
    
    def test_exception_paths_inherited_features(self):
        import api.organization_toggles_api as mod
        app = FastAPI()
        class ServiceThatRaises:
            async def get_rag_feature_toggles(self, org_id):
                raise Exception("Inherited features exception")
        app.dependency_overrides[mod.get_tenant_isolation_service] = lambda: ServiceThatRaises()
        app.dependency_overrides[mod.get_current_user] = lambda: {"id": "user-1", "role": "org_admin"}
        class DummyChecker:
            def __init__(self, *_a, **_k): pass
            def can_view_rag_features(self, *_a, **_k): return True
        mod.PermissionChecker = DummyChecker
        app.get('/api/v1/orgs/{org_id}/rag-toggles/inherited')(mod.get_inherited_rag_features)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/inherited')
            assert r.status_code == 500
    
    def test_exception_paths_summary(self):
        import api.organization_toggles_api as mod
        app = FastAPI()
        class ServiceThatRaises:
            async def get_rag_feature_toggles(self, org_id):
                raise Exception("Summary exception")
        app.dependency_overrides[mod.get_tenant_isolation_service] = lambda: ServiceThatRaises()
        app.dependency_overrides[mod.get_current_user] = lambda: {"id": "user-1", "role": "org_admin"}
        class DummyChecker:
            def __init__(self, *_a, **_k): pass
            def can_view_rag_features(self, *_a, **_k): return True
        mod.PermissionChecker = DummyChecker
        app.get('/api/v1/orgs/{org_id}/rag-toggles/summary')(mod.get_rag_toggle_summary)
        with TestClient(app) as c:
            r = c.get('/api/v1/orgs/org-123/rag-toggles/summary')
            assert r.status_code == 500
