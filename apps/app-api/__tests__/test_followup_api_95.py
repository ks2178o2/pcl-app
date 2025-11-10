"""
Comprehensive tests for Followup API
Target: 95% coverage for api/followup_api.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys
import os
import json
import asyncio
from datetime import datetime, timedelta
import importlib

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def mock_user():
    """Create a mock user"""
    return {
        "id": "user-123",
        "user_id": "user-123",
        "role": "salesperson",
        "organization_id": "org-123"
    }


@pytest.fixture
def mock_supabase():
    """Create a mock Supabase client"""
    mock_client = Mock()
    return mock_client


@pytest.fixture
def mock_semaphore():
    """Create a mock semaphore for rate limiting"""
    semaphore = AsyncMock()
    semaphore.__aenter__ = AsyncMock(return_value=None)
    semaphore.__aexit__ = AsyncMock(return_value=None)
    return semaphore


class TestBuildFollowupPrompt:
    """Tests for _build_followup_prompt function"""
    
    def test_build_followup_prompt_basic(self):
        """Test basic prompt building"""
        from api.followup_api import _build_followup_prompt
        
        transcript = "Test transcript"
        analysis_data = {
            "sentiment": {"overall": "positive", "customerEngagement": 7},
            "urgencyScoring": {"overallUrgency": 8},
            "customerPersonality": {"personalityType": "driver"},
            "objections": [{"id": "obj1", "type": "cost"}],
            "actionItems": [{"type": "follow-up"}]
        }
        
        prompt = _build_followup_prompt(
            transcript,
            analysis_data,
            "John Doe",
            "Jane Smith"
        )
        
        assert "John Doe" in prompt
        assert "Jane Smith" in prompt
        assert "positive" in prompt
        assert "driver" in prompt
        assert "Test transcript" in prompt
    
    def test_build_followup_prompt_minimal_data(self):
        """Test prompt building with minimal analysis data"""
        from api.followup_api import _build_followup_prompt
        
        transcript = "Short transcript"
        analysis_data = {}
        
        prompt = _build_followup_prompt(
            transcript,
            analysis_data,
            "Customer",
            "Salesperson"
        )
        
        assert "Customer" in prompt
        assert "Salesperson" in prompt
        assert "neutral" in prompt  # Default sentiment
        assert "5" in prompt  # Default engagement/urgency


class TestParseFollowupResponse:
    """Tests for _parse_followup_response function"""
    
    def test_parse_followup_response_valid_json(self):
        """Test parsing valid JSON response"""
        from api.followup_api import _parse_followup_response
        
        json_str = '{"strategy_type": "email", "priority_score": 8, "messages": []}'
        result = _parse_followup_response(json_str)
        
        assert result["strategy_type"] == "email"
        assert result["priority_score"] == 8
    
    def test_parse_followup_response_with_markdown_fences(self):
        """Test parsing JSON with markdown code fences"""
        from api.followup_api import _parse_followup_response
        
        json_str = '''```json
{"strategy_type": "email", "priority_score": 8}
```'''
        result = _parse_followup_response(json_str)
        
        assert result["strategy_type"] == "email"
        assert result["priority_score"] == 8
    
    def test_parse_followup_response_invalid_json(self):
        """Test parsing invalid JSON raises ValueError"""
        from api.followup_api import _parse_followup_response
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            _parse_followup_response("not valid json")
    
    def test_parse_followup_response_extract_between_braces(self):
        """Test extracting JSON between first { and last }"""
        from api.followup_api import _parse_followup_response
        
        json_str = 'Some text before {"strategy_type": "email"} Some text after'
        result = _parse_followup_response(json_str)
        
        assert result["strategy_type"] == "email"


class TestCalculateSendTime:
    """Tests for _calculate_send_time function"""
    
    def test_calculate_send_time_immediate(self):
        """Test immediate timing"""
        from api.followup_api import _calculate_send_time
        
        base_time = datetime(2025, 1, 1, 12, 0, 0)
        result = _calculate_send_time('immediate', base_time)
        
        assert result == base_time + timedelta(hours=1)
    
    def test_calculate_send_time_24_hours(self):
        """Test 24 hours timing"""
        from api.followup_api import _calculate_send_time
        
        base_time = datetime(2025, 1, 1, 12, 0, 0)
        result = _calculate_send_time('24_hours', base_time, day_offset=2)
        
        assert result == base_time + timedelta(days=3)
    
    def test_calculate_send_time_3_days(self):
        """Test 3 days timing"""
        from api.followup_api import _calculate_send_time
        
        base_time = datetime(2025, 1, 1, 12, 0, 0)
        result = _calculate_send_time('3_days', base_time)
        
        assert result == base_time + timedelta(days=3)
    
    def test_calculate_send_time_1_week(self):
        """Test 1 week timing"""
        from api.followup_api import _calculate_send_time
        
        base_time = datetime(2025, 1, 1, 12, 0, 0)
        result = _calculate_send_time('1_week', base_time)
        
        assert result == base_time + timedelta(days=7)
    
    def test_calculate_send_time_default(self):
        """Test default timing (unknown value)"""
        from api.followup_api import _calculate_send_time
        
        base_time = datetime(2025, 1, 1, 12, 0, 0)
        result = _calculate_send_time('unknown', base_time, day_offset=1)
        
        assert result == base_time + timedelta(days=2)  # 1 + 1


class TestGenerateFollowupPlan:
    """Tests for generate_followup_plan endpoint"""
    
    def _build_app_with_mocks(self, mock_user, supabase_mock=None, openai_mock=None, gemini_mock=None, settings_mock=None, semaphore_mock=None):
        """Build FastAPI app with mocked dependencies"""
        import importlib
        
        # Create mock functions
        def default_openai(prompt):
            return json.dumps({"strategy_type": "email", "messages": []})
        
        def default_gemini(prompt):
            return json.dumps({"strategy_type": "email", "messages": []})
        
        openai_func = openai_mock if openai_mock else default_openai
        gemini_func = gemini_mock if gemini_mock else default_gemini
        settings_result = settings_mock if settings_mock else (['openai', 'gemini'], ['openai', 'gemini'])
        semaphore = semaphore_mock if semaphore_mock else AsyncMock(__aenter__=AsyncMock(return_value=None), __aexit__=AsyncMock(return_value=None))
        
        # Patch the functions in call_center_followup_api (where they're actually defined)
        patches = []
        
        # Patch Supabase
        if supabase_mock:
            supabase_patch = patch('services.supabase_client.get_supabase_client', return_value=supabase_mock)
            supabase_patch.start()
            patches.append(supabase_patch)
        
        # Patch get_current_user
        auth_patch = patch('middleware.auth.get_current_user', return_value=mock_user)
        auth_patch.start()
        patches.append(auth_patch)
        
        # Patch the analysis functions in call_center_followup_api
        openai_patch = patch('api.call_center_followup_api._analyze_with_openai', side_effect=openai_func)
        openai_patch.start()
        patches.append(openai_patch)
        
        gemini_patch = patch('api.call_center_followup_api._analyze_with_gemini', side_effect=gemini_func)
        gemini_patch.start()
        patches.append(gemini_patch)
        
        settings_patch = patch('api.call_center_followup_api._get_org_analysis_settings', return_value=settings_result)
        settings_patch.start()
        patches.append(settings_patch)
        
        semaphore_patch = patch('api.call_center_followup_api.get_analysis_semaphore', return_value=semaphore)
        semaphore_patch.start()
        patches.append(semaphore_patch)
        
        # Reload followup_api to pick up the patches
        if 'api.followup_api' in sys.modules:
            followup_api = importlib.reload(sys.modules['api.followup_api'])
        else:
            import api.followup_api as followup_api
        
        app = FastAPI()
        app.include_router(followup_api.router)
        
        # Override dependencies
        app.dependency_overrides[followup_api.get_current_user] = lambda: mock_user
        
        # Store patches for cleanup
        app._test_patches = patches
        
        return app
    
    def _cleanup(self, app):
        """Clean up app dependencies and patches"""
        if hasattr(app, 'dependency_overrides'):
            app.dependency_overrides.clear()
        if hasattr(app, '_test_patches'):
            for patch_obj in app._test_patches:
                patch_obj.stop()
    
    def test_generate_followup_plan_missing_transcript(self, mock_user):
        """Test missing transcript returns 400"""
        app = self._build_app_with_mocks(mock_user)
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/followup/generate",
                    json={
                        "callRecordId": "call-123",
                        "analysisData": {"sentiment": {"overall": "positive"}},
                        "customerName": "John Doe",
                        "salespersonName": "Jane Smith"
                    }
                )
                assert response.status_code == 422  # Validation error
        finally:
            self._cleanup(app)
    
    def test_generate_followup_plan_missing_analysis_data(self, mock_user):
        """Test missing analysis data returns 400"""
        app = self._build_app_with_mocks(mock_user)
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/followup/generate",
                    json={
                        "callRecordId": "call-123",
                        "transcript": "Test transcript",
                        "customerName": "John Doe",
                        "salespersonName": "Jane Smith"
                    }
                )
                assert response.status_code == 422  # Validation error
        finally:
            self._cleanup(app)
    
    def test_generate_followup_plan_empty_transcript(self, mock_user):
        """Test empty transcript returns 400"""
        app = self._build_app_with_mocks(mock_user)
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/followup/generate",
                    json={
                        "callRecordId": "call-123",
                        "transcript": "",
                        "analysisData": {"sentiment": {"overall": "positive"}},
                        "customerName": "John Doe",
                        "salespersonName": "Jane Smith"
                    }
                )
                assert response.status_code == 400
        finally:
            self._cleanup(app)
    
    def test_generate_followup_plan_empty_analysis_data(self, mock_user):
        """Test empty analysis data returns 400"""
        app = self._build_app_with_mocks(mock_user)
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/followup/generate",
                    json={
                        "callRecordId": "call-123",
                        "transcript": "Test transcript",
                        "analysisData": {},
                        "customerName": "John Doe",
                        "salespersonName": "Jane Smith"
                    }
                )
                # Empty dict might pass validation, but let's check
                assert response.status_code in [400, 500]
        finally:
            self._cleanup(app)
    
    def test_generate_followup_plan_success(self, mock_user, mock_supabase):
        """Test successful followup plan generation"""
        llm_response = {
            "strategy_type": "email",
            "recommended_timing": "24_hours",
            "priority_score": 8,
            "customer_urgency": "high",
            "next_action": "Follow up",
            "reasoning": "Test reasoning",
            "messages": [
                {
                    "channel_type": "email",
                    "subject_line": "Test Subject",
                    "message_content": "Test message",
                    "tone": "professional",
                    "call_to_action": "Schedule consultation",
                    "estimated_send_time": "+1 day",
                    "status": "draft"
                }
            ]
        }
        
        def openai_mock(prompt):
            return json.dumps(llm_response)
        
        user_query = Mock()
        user_query.eq.return_value.execute.return_value = Mock(data=[{"organization_id": "org-123"}])
        settings_query = Mock()
        settings_query.eq.return_value.execute.return_value = Mock(data=[])
        
        def from_side_effect(table_name):
            query = Mock()
            if table_name == 'users':
                query.select.return_value = user_query
                return query
            elif table_name == 'organization_analysis_settings':
                query.select.return_value = settings_query
                return query
            elif table_name == 'follow_up_plans':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'select':
                        return Mock(data=[])
                    elif op == 'insert':
                        return Mock(data=[{"id": "plan-123"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.select.return_value = query
                query.eq.return_value = query
                query.delete.return_value = query
                query.insert.return_value = query
                def track_select(*args, **kwargs):
                    operation_tracker['op'] = 'select'
                    return query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.select = Mock(side_effect=track_select)
                query.insert = Mock(side_effect=track_insert)
                return query
            elif table_name == 'follow_up_messages':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'insert':
                        return Mock(data=[{"id": "msg-1"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.delete.return_value = query
                query.insert.return_value = query
                query.eq.return_value = query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.insert = Mock(side_effect=track_insert)
                return query
            return Mock()
        
        mock_supabase.from_.side_effect = from_side_effect
        
        app = self._build_app_with_mocks(mock_user, supabase_mock=mock_supabase, openai_mock=openai_mock)
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/followup/generate",
                    json={
                        "callRecordId": "call-123",
                        "transcript": "Test transcript",
                        "analysisData": {
                            "sentiment": {"overall": "positive"},
                            "urgencyScoring": {"overallUrgency": 8},
                            "customerPersonality": {"personalityType": "driver"}
                        },
                        "customerName": "John Doe",
                        "salespersonName": "Jane Smith"
                    }
                )
                assert response.status_code == 200
                assert response.json()["success"] is True
                assert "plan_id" in response.json()
        finally:
            self._cleanup(app)
    
    def test_generate_followup_plan_provider_failure(self, mock_user, mock_supabase):
        """Test when all providers fail"""
        def openai_mock(prompt):
            raise Exception("OpenAI API error")
        
        def gemini_mock(prompt):
            raise Exception("Gemini API error")
        
        user_query = Mock()
        user_query.eq.return_value.execute.return_value = Mock(data=[{"organization_id": "org-123"}])
        settings_query = Mock()
        settings_query.eq.return_value.execute.return_value = Mock(data=[{
            "provider_priority": ["openai", "gemini"],
            "enabled_providers": ["openai", "gemini"]
        }])
        
        def from_side_effect(table_name):
            query = Mock()
            if table_name == 'users':
                query.select.return_value = user_query
                return query
            elif table_name == 'organization_analysis_settings':
                query.select.return_value = settings_query
                return query
            return Mock()
        
        mock_supabase.from_.side_effect = from_side_effect
        
        app = self._build_app_with_mocks(
            mock_user,
            supabase_mock=mock_supabase,
            openai_mock=openai_mock,
            gemini_mock=gemini_mock,
            settings_mock=(['openai', 'gemini'], ['openai', 'gemini'])
        )
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/followup/generate",
                    json={
                        "callRecordId": "call-123",
                        "transcript": "Test transcript",
                        "analysisData": {
                            "sentiment": {"overall": "positive"}
                        },
                        "customerName": "John Doe",
                        "salespersonName": "Jane Smith"
                    }
                )
                assert response.status_code == 500
                assert "All providers failed" in response.json()["detail"]
        finally:
            self._cleanup(app)
    
    def test_generate_followup_plan_invalid_json_response(self, mock_user, mock_supabase):
        """Test when LLM returns invalid JSON"""
        def openai_mock(prompt):
            return "This is not valid JSON"
        
        user_query = Mock()
        user_query.eq.return_value.execute.return_value = Mock(data=[{"organization_id": "org-123"}])
        settings_query = Mock()
        settings_query.eq.return_value.execute.return_value = Mock(data=[])
        
        def from_side_effect(table_name):
            query = Mock()
            if table_name == 'users':
                query.select.return_value = user_query
                return query
            elif table_name == 'organization_analysis_settings':
                query.select.return_value = settings_query
                return query
            return Mock()
        
        mock_supabase.from_.side_effect = from_side_effect
        
        app = self._build_app_with_mocks(mock_user, supabase_mock=mock_supabase, openai_mock=openai_mock)
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/followup/generate",
                    json={
                        "callRecordId": "call-123",
                        "transcript": "Test transcript",
                        "analysisData": {
                            "sentiment": {"overall": "positive"}
                        },
                        "customerName": "John Doe",
                        "salespersonName": "Jane Smith"
                    }
                )
                assert response.status_code == 500
                assert "Failed to parse LLM response" in response.json()["detail"]
        finally:
            self._cleanup(app)
    
    def test_generate_followup_plan_with_existing_plan(self, mock_user, mock_supabase):
        """Test generating plan when one already exists (should delete old one)"""
        llm_response = {
            "strategy_type": "email",
            "recommended_timing": "24_hours",
            "priority_score": 8,
            "messages": [
                {
                    "channel_type": "email",
                    "message_content": "Test message",
                    "estimated_send_time": "+1 day",
                    "status": "draft"
                }
            ]
        }
        
        def openai_mock(prompt):
            return json.dumps(llm_response)
        
        user_query = Mock()
        user_query.eq.return_value.execute.return_value = Mock(data=[{"organization_id": "org-123"}])
        settings_query = Mock()
        settings_query.eq.return_value.execute.return_value = Mock(data=[])
        
        call_count = {'select': 0, 'delete_messages': 0, 'delete_plan': 0, 'insert': 0}
        
        def from_side_effect(table_name):
            query = Mock()
            if table_name == 'users':
                query.select.return_value = user_query
                return query
            elif table_name == 'organization_analysis_settings':
                query.select.return_value = settings_query
                return query
            elif table_name == 'follow_up_plans':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'select':
                        call_count['select'] += 1
                        if call_count['select'] == 1:
                            return Mock(data=[{"id": "old-plan-123"}])
                        return Mock(data=[])
                    elif op == 'delete':
                        call_count['delete_plan'] += 1
                        return Mock(data=[])
                    elif op == 'insert':
                        call_count['insert'] += 1
                        return Mock(data=[{"id": "new-plan-123"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.select.return_value = query
                query.eq.return_value = query
                query.delete.return_value = query
                query.insert.return_value = query
                def track_select(*args, **kwargs):
                    operation_tracker['op'] = 'select'
                    return query
                def track_delete(*args, **kwargs):
                    operation_tracker['op'] = 'delete'
                    return query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.select = Mock(side_effect=track_select)
                query.delete = Mock(side_effect=track_delete)
                query.insert = Mock(side_effect=track_insert)
                return query
            elif table_name == 'follow_up_messages':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'delete':
                        call_count['delete_messages'] += 1
                        return Mock(data=[])
                    elif op == 'insert':
                        return Mock(data=[{"id": "msg-1"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.delete.return_value = query
                query.insert.return_value = query
                query.eq.return_value = query
                def track_delete(*args, **kwargs):
                    operation_tracker['op'] = 'delete'
                    return query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.delete = Mock(side_effect=track_delete)
                query.insert = Mock(side_effect=track_insert)
                return query
            return Mock()
        
        mock_supabase.from_.side_effect = from_side_effect
        
        app = self._build_app_with_mocks(mock_user, supabase_mock=mock_supabase, openai_mock=openai_mock)
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/followup/generate",
                    json={
                        "callRecordId": "call-123",
                        "transcript": "Test transcript",
                        "analysisData": {
                            "sentiment": {"overall": "positive"}
                        },
                        "customerName": "John Doe",
                        "salespersonName": "Jane Smith"
                    }
                )
                assert response.status_code == 200
                # Verify old plan was deleted
                assert call_count['delete_messages'] == 1
                assert call_count['delete_plan'] == 1
        finally:
            self._cleanup(app)
    
    def test_generate_followup_plan_no_messages_fallback(self, mock_user, mock_supabase):
        """Test when LLM returns no messages (fallback to default message)"""
        llm_response = {
            "strategy_type": "email",
            "recommended_timing": "24_hours",
            "priority_score": 8,
            "messages": []  # No messages
        }
        
        def openai_mock(prompt):
            return json.dumps(llm_response)
        
        user_query = Mock()
        user_query.eq.return_value.execute.return_value = Mock(data=[{"organization_id": "org-123"}])
        settings_query = Mock()
        settings_query.eq.return_value.execute.return_value = Mock(data=[])
        
        def from_side_effect(table_name):
            query = Mock()
            if table_name == 'users':
                query.select.return_value = user_query
                return query
            elif table_name == 'organization_analysis_settings':
                query.select.return_value = settings_query
                return query
            elif table_name == 'follow_up_plans':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'select':
                        return Mock(data=[])
                    elif op == 'insert':
                        return Mock(data=[{"id": "plan-123"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.select.return_value = query
                query.eq.return_value = query
                query.delete.return_value = query
                query.insert.return_value = query
                def track_select(*args, **kwargs):
                    operation_tracker['op'] = 'select'
                    return query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.select = Mock(side_effect=track_select)
                query.insert = Mock(side_effect=track_insert)
                return query
            elif table_name == 'follow_up_messages':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'insert':
                        return Mock(data=[{"id": "msg-1"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.delete.return_value = query
                query.insert.return_value = query
                query.eq.return_value = query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.insert = Mock(side_effect=track_insert)
                return query
            return Mock()
        
        mock_supabase.from_.side_effect = from_side_effect
        
        app = self._build_app_with_mocks(mock_user, supabase_mock=mock_supabase, openai_mock=openai_mock)
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/followup/generate",
                    json={
                        "callRecordId": "call-123",
                        "transcript": "Test transcript",
                        "analysisData": {
                            "sentiment": {"overall": "positive"}
                        },
                        "customerName": "John Doe",
                        "salespersonName": "Jane Smith"
                    }
                )
                # Should succeed with fallback message
                assert response.status_code == 200
                assert response.json()["messages_count"] == 1
        finally:
            self._cleanup(app)
    
    def test_generate_followup_plan_timing_relative(self, mock_user, mock_supabase):
        """Test relative timing string (+1 day)"""
        llm_response = {
            "strategy_type": "email",
            "recommended_timing": "24_hours",
            "priority_score": 8,
            "messages": [
                {
                    "channel_type": "email",
                    "message_content": "Test message",
                    "estimated_send_time": "+2 days",
                    "status": "draft"
                }
            ]
        }
        
        def openai_mock(prompt):
            return json.dumps(llm_response)
        
        user_query = Mock()
        user_query.eq.return_value.execute.return_value = Mock(data=[{"organization_id": "org-123"}])
        settings_query = Mock()
        settings_query.eq.return_value.execute.return_value = Mock(data=[])
        
        def from_side_effect(table_name):
            query = Mock()
            if table_name == 'users':
                query.select.return_value = user_query
                return query
            elif table_name == 'organization_analysis_settings':
                query.select.return_value = settings_query
                return query
            elif table_name == 'follow_up_plans':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'select':
                        return Mock(data=[])
                    elif op == 'insert':
                        return Mock(data=[{"id": "plan-123"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.select.return_value = query
                query.eq.return_value = query
                query.delete.return_value = query
                query.insert.return_value = query
                def track_select(*args, **kwargs):
                    operation_tracker['op'] = 'select'
                    return query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.select = Mock(side_effect=track_select)
                query.insert = Mock(side_effect=track_insert)
                return query
            elif table_name == 'follow_up_messages':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'insert':
                        return Mock(data=[{"id": "msg-1"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.delete.return_value = query
                query.insert.return_value = query
                query.eq.return_value = query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.insert = Mock(side_effect=track_insert)
                return query
            return Mock()
        
        mock_supabase.from_.side_effect = from_side_effect
        
        app = self._build_app_with_mocks(mock_user, supabase_mock=mock_supabase, openai_mock=openai_mock)
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/followup/generate",
                    json={
                        "callRecordId": "call-123",
                        "transcript": "Test transcript",
                        "analysisData": {
                            "sentiment": {"overall": "positive"}
                        },
                        "customerName": "John Doe",
                        "salespersonName": "Jane Smith"
                    }
                )
                assert response.status_code == 200
        finally:
            self._cleanup(app)
    
    def test_generate_followup_plan_timing_iso(self, mock_user, mock_supabase):
        """Test ISO 8601 timing string"""
        llm_response = {
            "strategy_type": "email",
            "recommended_timing": "24_hours",
            "priority_score": 8,
            "messages": [
                {
                    "channel_type": "email",
                    "message_content": "Test message",
                    "estimated_send_time": "2025-01-10T14:00:00Z",
                    "status": "draft"
                }
            ]
        }
        
        def openai_mock(prompt):
            return json.dumps(llm_response)
        
        user_query = Mock()
        user_query.eq.return_value.execute.return_value = Mock(data=[{"organization_id": "org-123"}])
        settings_query = Mock()
        settings_query.eq.return_value.execute.return_value = Mock(data=[])
        
        def from_side_effect(table_name):
            query = Mock()
            if table_name == 'users':
                query.select.return_value = user_query
                return query
            elif table_name == 'organization_analysis_settings':
                query.select.return_value = settings_query
                return query
            elif table_name == 'follow_up_plans':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'select':
                        return Mock(data=[])
                    elif op == 'insert':
                        return Mock(data=[{"id": "plan-123"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.select.return_value = query
                query.eq.return_value = query
                query.delete.return_value = query
                query.insert.return_value = query
                def track_select(*args, **kwargs):
                    operation_tracker['op'] = 'select'
                    return query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.select = Mock(side_effect=track_select)
                query.insert = Mock(side_effect=track_insert)
                return query
            elif table_name == 'follow_up_messages':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'insert':
                        return Mock(data=[{"id": "msg-1"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.delete.return_value = query
                query.insert.return_value = query
                query.eq.return_value = query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.insert = Mock(side_effect=track_insert)
                return query
            return Mock()
        
        mock_supabase.from_.side_effect = from_side_effect
        
        app = self._build_app_with_mocks(mock_user, supabase_mock=mock_supabase, openai_mock=openai_mock)
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/followup/generate",
                    json={
                        "callRecordId": "call-123",
                        "transcript": "Test transcript",
                        "analysisData": {
                            "sentiment": {"overall": "positive"}
                        },
                        "customerName": "John Doe",
                        "salespersonName": "Jane Smith"
                    }
                )
                assert response.status_code == 200
        finally:
            self._cleanup(app)
    
    def test_generate_followup_plan_database_retry_missing_column(self, mock_user, mock_supabase):
        """Test database retry logic for missing columns"""
        llm_response = {
            "strategy_type": "email",
            "recommended_timing": "24_hours",
            "priority_score": 8,
            "messages": [
                {
                    "channel_type": "email",
                    "message_content": "Test message",
                    "estimated_send_time": "+1 day",
                    "status": "draft"
                }
            ]
        }
        
        def openai_mock(prompt):
            return json.dumps(llm_response)
        
        user_query = Mock()
        user_query.eq.return_value.execute.return_value = Mock(data=[{"organization_id": "org-123"}])
        settings_query = Mock()
        settings_query.eq.return_value.execute.return_value = Mock(data=[])
        
        call_count = {'insert': 0}
        
        def from_side_effect(table_name):
            query = Mock()
            if table_name == 'users':
                query.select.return_value = user_query
                return query
            elif table_name == 'organization_analysis_settings':
                query.select.return_value = settings_query
                return query
            elif table_name == 'follow_up_plans':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'select':
                        return Mock(data=[])
                    elif op == 'insert':
                        call_count['insert'] += 1
                        if call_count['insert'] == 1:
                            # First attempt fails with missing column error
                            error = Exception("could not find column 'customer_name'")
                            error_str = str(error)
                            raise Exception(f"pgrst204: {error_str}")
                        # Second attempt succeeds
                        return Mock(data=[{"id": "plan-123"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.select.return_value = query
                query.eq.return_value = query
                query.delete.return_value = query
                query.insert.return_value = query
                def track_select(*args, **kwargs):
                    operation_tracker['op'] = 'select'
                    return query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.select = Mock(side_effect=track_select)
                query.insert = Mock(side_effect=track_insert)
                return query
            elif table_name == 'follow_up_messages':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'insert':
                        return Mock(data=[{"id": "msg-1"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.delete.return_value = query
                query.insert.return_value = query
                query.eq.return_value = query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.insert = Mock(side_effect=track_insert)
                return query
            return Mock()
        
        mock_supabase.from_.side_effect = from_side_effect
        
        app = self._build_app_with_mocks(mock_user, supabase_mock=mock_supabase, openai_mock=openai_mock)
        try:
            with TestClient(app) as client:
                with patch('api.followup_api.logger'):
                    response = client.post(
                        "/api/followup/generate",
                        json={
                            "callRecordId": "call-123",
                            "transcript": "Test transcript",
                            "analysisData": {
                                "sentiment": {"overall": "positive"}
                            },
                            "customerName": "John Doe",
                            "salespersonName": "Jane Smith"
                        }
                    )
                    # Should succeed after retry
                    assert response.status_code == 200
        finally:
            self._cleanup(app)
    
    def test_generate_followup_plan_message_insert_fallback(self, mock_user, mock_supabase):
        """Test message insert fallback when message_data column doesn't exist"""
        llm_response = {
            "strategy_type": "email",
            "recommended_timing": "24_hours",
            "priority_score": 8,
            "messages": [
                {
                    "channel_type": "email",
                    "message_content": "Test message",
                    "estimated_send_time": "+1 day",
                    "status": "draft"
                }
            ]
        }
        
        def openai_mock(prompt):
            return json.dumps(llm_response)
        
        user_query = Mock()
        user_query.eq.return_value.execute.return_value = Mock(data=[{"organization_id": "org-123"}])
        settings_query = Mock()
        settings_query.eq.return_value.execute.return_value = Mock(data=[])
        
        call_count = {'insert': 0}
        
        def from_side_effect(table_name):
            query = Mock()
            if table_name == 'users':
                query.select.return_value = user_query
                return query
            elif table_name == 'organization_analysis_settings':
                query.select.return_value = settings_query
                return query
            elif table_name == 'follow_up_plans':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'select':
                        return Mock(data=[])
                    elif op == 'insert':
                        return Mock(data=[{"id": "plan-123"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.select.return_value = query
                query.eq.return_value = query
                query.delete.return_value = query
                query.insert.return_value = query
                def track_select(*args, **kwargs):
                    operation_tracker['op'] = 'select'
                    return query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.select = Mock(side_effect=track_select)
                query.insert = Mock(side_effect=track_insert)
                return query
            elif table_name == 'follow_up_messages':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'insert':
                        call_count['insert'] += 1
                        if call_count['insert'] == 1:
                            # First attempt fails with message_data column error
                            error = Exception("could not find column 'message_data'")
                            error_str = str(error)
                            raise Exception(f"pgrst204: {error_str}")
                        # Second attempt with minimal fields succeeds
                        return Mock(data=[{"id": "msg-1"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.delete.return_value = query
                query.insert.return_value = query
                query.eq.return_value = query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.insert = Mock(side_effect=track_insert)
                return query
            return Mock()
        
        mock_supabase.from_.side_effect = from_side_effect
        
        app = self._build_app_with_mocks(mock_user, supabase_mock=mock_supabase, openai_mock=openai_mock)
        try:
            with TestClient(app) as client:
                with patch('api.followup_api.logger'):
                    response = client.post(
                        "/api/followup/generate",
                        json={
                            "callRecordId": "call-123",
                            "transcript": "Test transcript",
                            "analysisData": {
                                "sentiment": {"overall": "positive"}
                            },
                            "customerName": "John Doe",
                            "salespersonName": "Jane Smith"
                        }
                    )
                    # Should succeed with fallback
                    assert response.status_code == 200
        finally:
            self._cleanup(app)
    
    def test_generate_followup_plan_provider_specific(self, mock_user, mock_supabase):
        """Test provider-specific selection"""
        llm_response = {
            "strategy_type": "email",
            "recommended_timing": "24_hours",
            "priority_score": 8,
            "messages": [
                {
                    "channel_type": "email",
                    "message_content": "Test message",
                    "estimated_send_time": "+1 day",
                    "status": "draft"
                }
            ]
        }
        
        def openai_mock(prompt):
            return json.dumps(llm_response)
        
        user_query = Mock()
        user_query.eq.return_value.execute.return_value = Mock(data=[{"organization_id": "org-123"}])
        settings_query = Mock()
        settings_query.eq.return_value.execute.return_value = Mock(data=[{
            "provider_priority": ["openai", "gemini"],
            "enabled_providers": ["openai", "gemini"]
        }])
        
        def from_side_effect(table_name):
            query = Mock()
            if table_name == 'users':
                query.select.return_value = user_query
                return query
            elif table_name == 'organization_analysis_settings':
                query.select.return_value = settings_query
                return query
            elif table_name == 'follow_up_plans':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'select':
                        return Mock(data=[])
                    elif op == 'insert':
                        return Mock(data=[{"id": "plan-123"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.select.return_value = query
                query.eq.return_value = query
                query.delete.return_value = query
                query.insert.return_value = query
                def track_select(*args, **kwargs):
                    operation_tracker['op'] = 'select'
                    return query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.select = Mock(side_effect=track_select)
                query.insert = Mock(side_effect=track_insert)
                return query
            elif table_name == 'follow_up_messages':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'insert':
                        return Mock(data=[{"id": "msg-1"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.delete.return_value = query
                query.insert.return_value = query
                query.eq.return_value = query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.insert = Mock(side_effect=track_insert)
                return query
            return Mock()
        
        mock_supabase.from_.side_effect = from_side_effect
        
        app = self._build_app_with_mocks(
            mock_user,
            supabase_mock=mock_supabase,
            openai_mock=openai_mock,
            settings_mock=(['openai', 'gemini'], ['openai', 'gemini'])
        )
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/followup/generate",
                    json={
                        "callRecordId": "call-123",
                        "transcript": "Test transcript",
                        "analysisData": {
                            "sentiment": {"overall": "positive"}
                        },
                        "customerName": "John Doe",
                        "salespersonName": "Jane Smith",
                        "provider": "openai"  # Specific provider
                    }
                )
                assert response.status_code == 200
                assert response.json()["provider"] == "openai"
        finally:
            self._cleanup(app)
    
    def test_generate_followup_plan_provider_auto(self, mock_user, mock_supabase):
        """Test provider auto selection"""
        llm_response = {
            "strategy_type": "email",
            "recommended_timing": "24_hours",
            "priority_score": 8,
            "messages": [
                {
                    "channel_type": "email",
                    "message_content": "Test message",
                    "estimated_send_time": "+1 day",
                    "status": "draft"
                }
            ]
        }
        
        def gemini_mock(prompt):
            return json.dumps(llm_response)
        
        user_query = Mock()
        user_query.eq.return_value.execute.return_value = Mock(data=[{"organization_id": "org-123"}])
        settings_query = Mock()
        settings_query.eq.return_value.execute.return_value = Mock(data=[{
            "provider_priority": ["gemini", "openai"],
            "enabled_providers": ["gemini", "openai"]
        }])
        
        def from_side_effect(table_name):
            query = Mock()
            if table_name == 'users':
                query.select.return_value = user_query
                return query
            elif table_name == 'organization_analysis_settings':
                query.select.return_value = settings_query
                return query
            elif table_name == 'follow_up_plans':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'select':
                        return Mock(data=[])
                    elif op == 'insert':
                        return Mock(data=[{"id": "plan-123"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.select.return_value = query
                query.eq.return_value = query
                query.delete.return_value = query
                query.insert.return_value = query
                def track_select(*args, **kwargs):
                    operation_tracker['op'] = 'select'
                    return query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.select = Mock(side_effect=track_select)
                query.insert = Mock(side_effect=track_insert)
                return query
            elif table_name == 'follow_up_messages':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'insert':
                        return Mock(data=[{"id": "msg-1"}])
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.delete.return_value = query
                query.insert.return_value = query
                query.eq.return_value = query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.insert = Mock(side_effect=track_insert)
                return query
            return Mock()
        
        mock_supabase.from_.side_effect = from_side_effect
        
        app = self._build_app_with_mocks(
            mock_user,
            supabase_mock=mock_supabase,
            gemini_mock=gemini_mock,
            settings_mock=(['gemini', 'openai'], ['gemini', 'openai'])
        )
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/followup/generate",
                    json={
                        "callRecordId": "call-123",
                        "transcript": "Test transcript",
                        "analysisData": {
                            "sentiment": {"overall": "positive"}
                        },
                        "customerName": "John Doe",
                        "salespersonName": "Jane Smith",
                        "provider": "auto"
                    }
                )
                assert response.status_code == 200
                assert response.json()["provider"] == "gemini"
        finally:
            self._cleanup(app)
    
    def test_generate_followup_plan_plan_data_empty(self, mock_user, mock_supabase):
        """Test when plan_data is empty"""
        def openai_mock(prompt):
            return json.dumps({})  # Empty dict
        
        user_query = Mock()
        user_query.eq.return_value.execute.return_value = Mock(data=[{"organization_id": "org-123"}])
        settings_query = Mock()
        settings_query.eq.return_value.execute.return_value = Mock(data=[])
        
        def from_side_effect(table_name):
            query = Mock()
            if table_name == 'users':
                query.select.return_value = user_query
                return query
            elif table_name == 'organization_analysis_settings':
                query.select.return_value = settings_query
                return query
            return Mock()
        
        mock_supabase.from_.side_effect = from_side_effect
        
        app = self._build_app_with_mocks(mock_user, supabase_mock=mock_supabase, openai_mock=openai_mock)
        try:
            with TestClient(app) as client:
                response = client.post(
                    "/api/followup/generate",
                    json={
                        "callRecordId": "call-123",
                        "transcript": "Test transcript",
                        "analysisData": {
                            "sentiment": {"overall": "positive"}
                        },
                        "customerName": "John Doe",
                        "salespersonName": "Jane Smith"
                    }
                )
                # Should fail - empty plan_data
                assert response.status_code == 500
        finally:
            self._cleanup(app)
    
    def test_generate_followup_plan_database_error(self, mock_user, mock_supabase):
        """Test database error handling"""
        llm_response = {
            "strategy_type": "email",
            "recommended_timing": "24_hours",
            "priority_score": 8,
            "messages": [
                {
                    "channel_type": "email",
                    "message_content": "Test message",
                    "estimated_send_time": "+1 day",
                    "status": "draft"
                }
            ]
        }
        
        def openai_mock(prompt):
            return json.dumps(llm_response)
        
        user_query = Mock()
        user_query.eq.return_value.execute.return_value = Mock(data=[{"organization_id": "org-123"}])
        settings_query = Mock()
        settings_query.eq.return_value.execute.return_value = Mock(data=[])
        
        def from_side_effect(table_name):
            query = Mock()
            if table_name == 'users':
                query.select.return_value = user_query
                return query
            elif table_name == 'organization_analysis_settings':
                query.select.return_value = settings_query
                return query
            elif table_name == 'follow_up_plans':
                operation_tracker = {'op': None}
                def execute_side_effect():
                    op = operation_tracker['op']
                    if op == 'select':
                        return Mock(data=[])
                    elif op == 'insert':
                        raise Exception("Database connection failed")
                    return Mock(data=[])
                query.execute = Mock(side_effect=execute_side_effect)
                query.select.return_value = query
                query.eq.return_value = query
                query.delete.return_value = query
                query.insert.return_value = query
                def track_select(*args, **kwargs):
                    operation_tracker['op'] = 'select'
                    return query
                def track_insert(*args, **kwargs):
                    operation_tracker['op'] = 'insert'
                    return query
                query.select = Mock(side_effect=track_select)
                query.insert = Mock(side_effect=track_insert)
                return query
            return Mock()
        
        mock_supabase.from_.side_effect = from_side_effect
        
        app = self._build_app_with_mocks(mock_user, supabase_mock=mock_supabase, openai_mock=openai_mock)
        try:
            with TestClient(app) as client:
                with patch('api.followup_api.logger'):
                    response = client.post(
                        "/api/followup/generate",
                        json={
                            "callRecordId": "call-123",
                            "transcript": "Test transcript",
                            "analysisData": {
                                "sentiment": {"overall": "positive"}
                            },
                            "customerName": "John Doe",
                            "salespersonName": "Jane Smith"
                        }
                    )
                    # Should fail with database error
                    assert response.status_code == 500
                    assert "Failed to save follow-up plan" in response.json()["detail"]
        finally:
            self._cleanup(app)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

