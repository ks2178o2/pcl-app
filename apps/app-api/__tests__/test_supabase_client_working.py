# apps/app-api/__tests__/test_supabase_client_working.py

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from supabase import Client

from services.supabase_client import SupabaseClientManager, get_supabase_client


class TestSupabaseClientWorking:
    """Working tests for Supabase Client Manager"""
    
    @pytest.fixture
    def manager(self):
        """Create fresh manager instance"""
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        return SupabaseClientManager()
    
    def test_singleton_pattern(self, manager):
        """Test singleton pattern - lines 17-20"""
        manager2 = SupabaseClientManager()
        assert manager is manager2
    
    def test_get_client_success(self, manager):
        """Test getting client successfully - lines 22-38"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            mock_client = Mock(spec=Client)
            with patch('services.supabase_client.create_client', return_value=mock_client):
                client = manager.get_client()
                assert client == mock_client
    
    def test_get_client_missing_url(self, manager):
        """Test get client when URL is missing - line 29"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                manager.get_client()
            assert "SUPABASE_URL" in str(exc_info.value)
    
    def test_get_client_missing_key(self, manager):
        """Test get client when key is missing - line 29"""
        with patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co'}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                manager.get_client()
            assert "SUPABASE_SERVICE_ROLE_KEY" in str(exc_info.value)
    
    def test_get_client_exception(self, manager):
        """Test get client when create fails - lines 34-36"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            with patch('services.supabase_client.create_client', side_effect=Exception("Connection failed")):
                with pytest.raises(Exception) as exc_info:
                    manager.get_client()
                assert "Connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, manager):
        """Test health check when healthy - lines 40-57"""
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = [{'id': 'profile-123'}]
        
        mock_query = Mock()
        mock_query.limit.return_value.execute.return_value = mock_result
        mock_client.from_.return_value.select.return_value = mock_query
        
        with patch.object(manager, '_client', mock_client):
            with patch.object(manager, 'get_client', return_value=mock_client):
                result = await manager.health_check()
                
                assert result['success'] is True
                assert result['status'] == 'healthy'
    
    @pytest.mark.asyncio
    async def test_health_check_exception(self, manager):
        """Test health check when fails - line 53"""
        mock_client = Mock()
        mock_client.from_.side_effect = Exception("DB error")
        
        with patch.object(manager, 'get_client', return_value=mock_client):
            result = await manager.health_check()
            
            assert result['success'] is False
            assert result['status'] == 'unhealthy'
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_execute_query_with_filters(self, manager):
        """Test execute query with filters - lines 59-79"""
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = [{'id': '1', 'name': 'test'}]
        
        mock_query = Mock()
        mock_query.eq.return_value.execute.return_value = mock_result
        
        with patch.object(manager, 'get_client', return_value=mock_client):
            mock_client.from_.return_value.select.return_value = mock_query
            
            result = await manager.execute_query('profiles', select='id', filters={'organization_id': 'org-123'})
            
            assert result['success'] is True
            assert len(result['data']) == 1
    
    @pytest.mark.asyncio
    async def test_execute_query_exception(self, manager):
        """Test execute query exception - line 76"""
        mock_client = Mock()
        mock_client.from_.side_effect = Exception("Query failed")
        
        with patch.object(manager, 'get_client', return_value=mock_client):
            result = await manager.execute_query('profiles')
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_insert_data_success(self, manager):
        """Test insert data successfully - lines 81-95"""
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = [{'id': 'new-123', 'name': 'test'}]
        
        mock_insert = Mock()
        mock_insert.execute.return_value = mock_result
        mock_client.from_.return_value.insert.return_value = mock_insert
        
        with patch.object(manager, 'get_client', return_value=mock_client):
            result = await manager.insert_data('profiles', {'name': 'test'})
            
            assert result['success'] is True
            assert result['data'] == [{'id': 'new-123', 'name': 'test'}]
    
    @pytest.mark.asyncio
    async def test_insert_data_exception(self, manager):
        """Test insert data exception - line 92"""
        mock_client = Mock()
        mock_client.from_.side_effect = Exception("Insert failed")
        
        with patch.object(manager, 'get_client', return_value=mock_client):
            result = await manager.insert_data('profiles', {'name': 'test'})
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_update_data_success(self, manager):
        """Test update data successfully - lines 97-116"""
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = [{'id': '1', 'name': 'updated'}]
        
        mock_query = Mock()
        mock_query.eq.return_value.execute.return_value = mock_result
        
        with patch.object(manager, 'get_client', return_value=mock_client):
            mock_client.from_.return_value.update.return_value = mock_query
            
            result = await manager.update_data('profiles', {'name': 'updated'}, {'id': '1'})
            
            assert result['success'] is True
            assert result['data'] == [{'id': '1', 'name': 'updated'}]
    
    @pytest.mark.asyncio
    async def test_update_data_exception(self, manager):
        """Test update data exception - line 113"""
        mock_client = Mock()
        mock_client.from_.side_effect = Exception("Update failed")
        
        with patch.object(manager, 'get_client', return_value=mock_client):
            result = await manager.update_data('profiles', {'name': 'updated'}, {'id': '1'})
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_delete_data_success(self, manager):
        """Test delete data successfully - lines 118-137"""
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = [{'id': '1'}]
        
        mock_query = Mock()
        mock_query.eq.return_value.execute.return_value = mock_result
        
        with patch.object(manager, 'get_client', return_value=mock_client):
            mock_client.from_.return_value.delete.return_value = mock_query
            
            result = await manager.delete_data('profiles', {'id': '1'})
            
            assert result['success'] is True
            assert result['deleted_count'] == 1
    
    @pytest.mark.asyncio
    async def test_delete_data_exception(self, manager):
        """Test delete data exception - line 134"""
        mock_client = Mock()
        mock_client.from_.side_effect = Exception("Delete failed")
        
        with patch.object(manager, 'get_client', return_value=mock_client):
            result = await manager.delete_data('profiles', {'id': '1'})
            
            assert result['success'] is False
            assert 'error' in result
    
    def test_get_supabase_client_function(self):
        """Test get_supabase_client function - lines 140-143"""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test-key'
        }):
            mock_client = Mock(spec=Client)
            with patch('services.supabase_client.create_client', return_value=mock_client):
                client = get_supabase_client()
                assert client == mock_client


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=services.supabase_client', '--cov-report=html'])

