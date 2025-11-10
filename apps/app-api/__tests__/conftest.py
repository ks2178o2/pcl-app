import pytest
from pathlib import Path
import sys
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load test environment variables (prefer .env.test over .env for tests)
# This ensures tests use test database credentials, not production
try:
    from dotenv import load_dotenv
    # Prefer .env.test for tests to use test database credentials
    env_paths = [
        PROJECT_ROOT / '.env.test',  # Test-specific credentials (preferred)
        PROJECT_ROOT / 'sandbox.env',  # Sandbox credentials
        PROJECT_ROOT / '.env',  # Development credentials (fallback)
        PROJECT_ROOT.parent.parent / '.env.test',  # Root .env.test
        PROJECT_ROOT.parent.parent / '.env',  # Root .env
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path, override=False)  # Don't override if already set
            break
except ImportError:
    pass  # dotenv not available, rely on environment

# Archived integration suites (renamed with `arch_` prefix). We keep the notes
# here as institutional memory in case we ever revive these flows.
ARCHIVED_MODULE_NOTES = {
    # Analysis
    "arch_test_analysis_api.py": "Legacy analysis API suite expects Supabase-backed helpers that were removed; rewrite completely against the simplified /api/analysis endpoint (REWRITE).",
    "arch_test_analysis_api_retry_and_settings.py": "Depends on legacy analysis settings endpoints; redesign alongside new analysis workflow (REWRITE).",
    # Audit
    "arch_test_audit_performance_exception.py": "Targets deprecated performance codepaths removed from audit service; no longer relevant (RETIRE).",
    "arch_test_audit_performance_final.py": "Covers legacy high-throughput audit optimisations that were stripped; retire instead of fixing (RETIRE).",
    "arch_test_audit_service.py": "Giant legacy audit suite bound to Supabase tables; requires full rewrite around the simplified audit logger (REWRITE).",
    "arch_test_audit_service_95_push.py": "Complement to legacy audit suite; remove in favour of lean targeted tests (REWRITE).",
    "arch_test_audit_service_comprehensive.py": "Legacy coverage harness assuming historical schema; rewrite from scratch (REWRITE).",
    "arch_test_audit_service_improved.py": "Legacy audit smoke tests duplicating removed behaviour; safe to retire (RETIRE).",
    "arch_test_audit_service_performance_exception.py": "Focuses on abandoned performance routines; retire (RETIRE).",
    "arch_test_audit_service_final_coverage.py": "Legacy audit coverage aggregator; retire (RETIRE).",
    "arch_test_audit_service_final_lines.py": "Depends on legacy Supabase schema and file exports removed from current audit service; retire (RETIRE).",
    "arch_test_comprehensive_services.py": "Broad integration suite targeting deprecated service graph; retire and replace with module-focused tests (RETIRE).",
    # Auth
    "arch_test_auth_2fa_api.py": "Old auth flows hitting endpoints deleted in v1.0.6; rewrite only if reinstating those endpoints (REWRITE).",
    "arch_test_auth_api.py": "Targets legacy auth endpoints replaced by Supabase Auth; rewrite small subset for new flows (REWRITE).",
    "arch_test_auth_flows_complete.py": "Full-stack auth journey relying on live Supabase DB; create a fresh e2e test harness instead (REWRITE).",
    "arch_test_auth_integration.py": "Same as above real Supabase coverage; rebuild with modern sign-in/out flow mocking (REWRITE).",
    "arch_test_auth_integration_real.py": "Real DB variant of legacy auth tests; retire to avoid hitting production keys (RETIRE).",
    # Bulk import / call analysis
    "arch_test_bulk_import_service_95.py": "Bulk import service has been slimmed down; legacy supabase-heavy suite needs complete rewrite (REWRITE).",
    "arch_test_call_analysis_service_95.py": "Legacy LLM orchestration tests gone out of sync with minimal analysis service; rewrite if feature resurfaces (REWRITE).",
    # Context manager & enhanced context
    "arch_test_context_manager_85_coverage.py": "Contexts now simplified; legacy coverage depends on removed caching layers (REWRITE).",
    "arch_test_context_manager_95.py": "Duplicate legacy context tests; rewrite targeted unit tests instead (REWRITE).",
    "arch_test_context_manager_95_coverage.py": "Legacy supabase integration harness; retire (RETIRE).",
    "arch_test_context_manager_additional_coverage.py": "Additional coverage for the old architecture; retire (RETIRE).",
    "arch_test_context_manager_comprehensive.py": "Massive legacy context suite; rebuild for current lightweight manager (REWRITE).",
    "arch_test_context_manager_coverage_gaps.py": "Documentation-driven gaps for legacy code; retire (RETIRE).",
    "arch_test_context_manager_gaps_95.py": "Same as above; retire (RETIRE).",
    "arch_test_context_manager_improved.py": "Legacy improvement harness; retire (RETIRE).",
    # ElevenLabs / Email
    "arch_test_elevenlabs_rvm_service_95.py": "Integrates with ElevenLabs RVM service deprecated from product; retire (RETIRE).",
    "arch_test_email_service_95.py": "Exercises removed transactional email pipeline; retire (RETIRE).",
    # Enhanced context / RAG suites
    "arch_test_enhanced_context_95_complete.py": "Legacy RAG ingestion workflow; requires full redesign for current minimal implementation (REWRITE).",
    "arch_test_enhanced_context_95_complete_final.py": "Companion to the above; rewrite alongside new ingestion strategy (REWRITE).",
    "arch_test_enhanced_context_95_coverage.py": "Legacy coverage harness for superseded features; retire (RETIRE).",
    "arch_test_enhanced_context_95_final.py": "Legacy suite expecting old Supabase schema; retire (RETIRE).",
    "arch_test_enhanced_context_95_final_push.py": "Follow-up to legacy harness; retire (RETIRE).",
    "arch_test_enhanced_context_95_perfect.py": "Legacy perfect coverage extension; retire (RETIRE).",
    "arch_test_enhanced_context_95_push.py": "Legacy push harness; retire (RETIRE).",
    "arch_test_enhanced_context_95_target.py": "Legacy target coverage; retire (RETIRE).",
    "arch_test_enhanced_context_95_ultimate.py": "Legacy ultimate coverage; retire (RETIRE).",
    "arch_test_enhanced_context_api_client.py": "Depends on endpoints removed with enhanced context rewrite; rewrite when new API stabilises (REWRITE).",
    "arch_test_enhanced_context_coverage_gaps.py": "Legacy coverage gaps doc; retire (RETIRE).",
    "arch_test_enhanced_context_final_gaps.py": "Legacy final gaps; retire (RETIRE).",
    "arch_test_enhanced_context_management.py": "Legacy management workflows; rewrite atop new context manager (REWRITE).",
    "arch_test_enhanced_context_management_fixed.py": "Companion harness for legacy management; retire (RETIRE).",
    "arch_test_enhanced_context_management_simple.py": "Simplified variant still relying on old schema; retire (RETIRE).",
    "arch_test_enhanced_context_manager_95_coverage.py": "Legacy coverage for manager; rewrite targeted unit tests (REWRITE).",
    "arch_test_enhanced_context_manager_additional_coverage.py": "Legacy add-on coverage; retire (RETIRE).",
    "arch_test_enhanced_context_manager_comprehensive.py": "Legacy comprehensive suite; rewrite (REWRITE).",
    "arch_test_enhanced_context_manager_gaps_95.py": "Legacy gap tracker; retire (RETIRE).",
    "arch_test_enhanced_context_manager_working.py": "Legacy smoke tests; retire (RETIRE).",
    "arch_test_feature_inheritance_service_95.py": "Legacy inheritance logic removed with hierarchy simplification; rewrite only if feature returns (REWRITE).",
    "arch_test_feature_inheritance_working.py": "Legacy inheritance smoke tests; retire (RETIRE).",
    # Invitations & permissions
    "arch_test_invitations_api.py": "Hits legacy invitations endpoints removed from FastAPI app; rewrite when new onboarding API exists (REWRITE).",
    "arch_test_invitations_api_endpoints.py": "Real Supabase integration test for deprecated invitations API; retire (RETIRE).",
    "arch_test_permissions_convenience_decorators.py": "Legacy permission decorators no longer present; retire (RETIRE).",
    "arch_test_permissions_decorators_95.py": "Legacy permissions harness; rewrite minimal coverage for current middleware (REWRITE).",
    "arch_test_permissions_decorators_integration.py": "Integration suite for older permissions graph; retire (RETIRE).",
    "arch_test_permissions_validate_95.py": "Legacy validation pipeline; replace with focused tests on current validation middleware (REWRITE).",
    "arch_test_permissions_validate_95_final.py": "Legacy final coverage; retire (RETIRE).",
    "arch_test_permissions_validate_function.py": "Legacy helper tests; retire (RETIRE).",
    # RAG APIs
    "arch_test_rag_feature_api_endpoints.py": "Legacy RAG API endpoints removed; rewrite once new endpoints finalised (REWRITE).",
    "arch_test_rag_feature_integration.py": "Legacy integration harness reliant on old Supabase schemas; retire (RETIRE).",
    "arch_test_rag_feature_management_comprehensive.py": "Legacy management suite; rewrite for current lightweight implementation (REWRITE).",
    "arch_test_rag_features_api_95.py": "Legacy REST API coverage; retire (RETIRE).",
    "arch_test_rag_features_api_95_fixed.py": "Legacy fixed harness; retire (RETIRE).",
    "arch_test_rag_features_api_client.py": "Legacy client-level tests; retire (RETIRE).",
    "arch_test_rag_features_comprehensive.py": "Targets validation helpers that no longer exist in new middleware; rewrite focused tests for current implementation (REWRITE).",
    "arch_test_rag_features_e2e.py": "End-to-end workflow built around previous Supabase schema; retire pending new RAG workflows (RETIRE).",
    "arch_test_twilio_api_95.py": "Legacy Twilio integration harness relying on removed call center flows; retire (RETIRE).",
}


def pytest_collection_modifyitems(config, items):
    for item in items:
        module_name = Path(item.fspath).name
        reason = ARCHIVED_MODULE_NOTES.get(module_name)
        if reason:
            item.add_marker(pytest.mark.skip(reason=reason))


# Stub Supabase client for unit tests
class StubSupabase:
    def __init__(self, responses=None):
        self._responses = responses if responses is not None else {}
        self.from_calls = []
        self.select_calls = []
        self.eq_calls = []
        self.insert_calls = []
        self.update_calls = []
        self.delete_calls = []

    def from_(self, table_name):
        self.from_calls.append(table_name)
        return StubSupabase.StubQuery(table_name, self._responses, self)

    def table(self, table_name):
        self.from_calls.append(table_name) # Use from_calls for table as well
        return StubSupabase.StubQuery(table_name, self._responses, self)

    class StubQuery:
        def __init__(self, table_name, responses, parent_stub):
            self.table_name = table_name
            self.responses = responses
            self.parent_stub = parent_stub
            self.filters = {}
            self.selected_fields = None
            self.single_mode = False
            self.order_by = None
            self.limit_val = None

        def select(self, fields):
            self.selected_fields = fields
            self.parent_stub.select_calls.append((self.table_name, fields))
            return self

        def eq(self, column, value):
            self.filters[column] = value
            self.parent_stub.eq_calls.append((self.table_name, column, value))
            return self

        def order(self, column, **kwargs):
            self.order_by = (column, kwargs)
            return self

        def limit(self, value):
            self.limit_val = value
            return self

        def single(self):
            self.single_mode = True
            return self

        def insert(self, data):
            self.parent_stub.insert_calls.append((self.table_name, data))
            return self

        def update(self, data):
            self.parent_stub.update_calls.append((self.table_name, data, self.filters))
            return self

        def delete(self):
            self.parent_stub.delete_calls.append((self.table_name, self.filters))
            return self

        def execute(self):
            # Simple response logic: return data if table_name matches and filters are met
            if self.table_name in self.responses:
                for response_set in self.responses[self.table_name]:
                    match = True
                    for col, val in self.filters.items():
                        # Check if the response set contains a dictionary that matches the filter
                        if not any(item.get(col) == val for item in response_set):
                            match = False
                            break
                    if match:
                        data = response_set
                        if self.single_mode and data:
                            from unittest.mock import Mock
                            return Mock(data=data[0], count=len(data))
                        from unittest.mock import Mock
                        return Mock(data=data, count=len(data))
            from unittest.mock import Mock
            return Mock(data=[], count=0)


@pytest.fixture
def stub_supabase():
    return StubSupabase()
