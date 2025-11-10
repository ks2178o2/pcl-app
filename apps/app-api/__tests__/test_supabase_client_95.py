"""
Tests for supabase_client.py to achieve 95% coverage
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import os
from services.supabase_client import SupabaseClientManager, get_supabase_client


class TestSupabaseClientManager:
    """Test SupabaseClientManager"""
    
    def test_singleton_pattern(self):
        """Test that SupabaseClientManager is a singleton"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        manager1 = SupabaseClientManager()
        manager2 = SupabaseClientManager()
        
        assert manager1 is manager2
    
    @patch('services.supabase_client.create_client')
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_SERVICE_ROLE_KEY': 'test_key'})
    def test_get_client_success(self, mock_create_client):
        """Test successful client creation"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        manager = SupabaseClientManager()
        client = manager.get_client()
        
        assert client is mock_client
        mock_create_client.assert_called_once_with('https://test.supabase.co', 'test_key')
    
    @patch('services.supabase_client.create_client')
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co'}, clear=True)
    def test_get_client_no_key(self, mock_create_client):
        """Test client creation when no key is set"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        manager = SupabaseClientManager()
        client = manager.get_client()
        
        assert client is None
        mock_create_client.assert_not_called()
    
    @patch('services.supabase_client.create_client')
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_SERVICE_KEY': 'fallback_key'}, clear=True)
    def test_get_client_fallback_key(self, mock_create_client):
        """Test client creation with fallback SUPABASE_SERVICE_KEY"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        manager = SupabaseClientManager()
        client = manager.get_client()
        
        assert client is mock_client
        mock_create_client.assert_called_once_with('https://test.supabase.co', 'fallback_key')
    
    @patch('services.supabase_client.create_client')
    @patch.dict(os.environ, {'SUPABASE_SERVICE_ROLE_KEY': 'test_key'}, clear=True)
    def test_get_client_default_url(self, mock_create_client):
        """Test client creation with default URL"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        manager = SupabaseClientManager()
        client = manager.get_client()
        
        assert client is mock_client
        # Check that default URL is used
        call_args = mock_create_client.call_args[0]
        assert 'supabase.co' in call_args[0]
    
    @patch('services.supabase_client.create_client')
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_SERVICE_ROLE_KEY': 'test_key'})
    def test_get_client_exception(self, mock_create_client):
        """Test client creation when create_client raises exception"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        mock_create_client.side_effect = Exception("Connection failed")
        
        manager = SupabaseClientManager()
        client = manager.get_client()
        
        assert client is None
    
    @patch('services.supabase_client.create_client')
    @patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_SERVICE_ROLE_KEY': 'test_key'})
    def test_get_client_cached(self, mock_create_client):
        """Test that client is cached after first creation"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        manager = SupabaseClientManager()
        client1 = manager.get_client()
        client2 = manager.get_client()
        
        assert client1 is client2
        assert mock_create_client.call_count == 1  # Only called once
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = [{'id': 'test'}]
        mock_query = Mock()
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.execute = Mock(return_value=mock_result)
        mock_select = Mock()
        mock_select.select = Mock(return_value=mock_query)
        mock_client.from_ = Mock(return_value=mock_select)
        
        with patch('services.supabase_client.create_client', return_value=mock_client):
            with patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_SERVICE_ROLE_KEY': 'test_key'}):
                manager = SupabaseClientManager()
                result = await manager.health_check()
                
                assert result['success'] is True
                assert result['status'] == 'healthy'
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check when client is None"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        with patch.dict(os.environ, {}, clear=True):
            manager = SupabaseClientManager()
            result = await manager.health_check()
            
            assert result['success'] is False
            assert result['status'] == 'unhealthy'
    
    @pytest.mark.asyncio
    async def test_health_check_exception(self):
        """Test health check when query raises exception"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        mock_client = Mock()
        mock_query = Mock()
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.execute = Mock(side_effect=Exception("Query failed"))
        mock_select = Mock()
        mock_select.select = Mock(return_value=mock_query)
        mock_client.from_ = Mock(return_value=mock_select)
        
        with patch('services.supabase_client.create_client', return_value=mock_client):
            with patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_SERVICE_ROLE_KEY': 'test_key'}):
                manager = SupabaseClientManager()
                result = await manager.health_check()
                
                assert result['success'] is False
                assert result['status'] == 'unhealthy'
                assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_execute_query_success(self):
        """Test successful execute_query"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = [{'id': '1', 'name': 'Test'}]
        mock_query = Mock()
        mock_query.eq = Mock(return_value=mock_query)
        mock_query.execute = Mock(return_value=mock_result)
        mock_select = Mock()
        mock_select.select = Mock(return_value=mock_query)
        mock_client.from_ = Mock(return_value=mock_select)
        
        with patch('services.supabase_client.create_client', return_value=mock_client):
            with patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_SERVICE_ROLE_KEY': 'test_key'}):
                manager = SupabaseClientManager()
                result = await manager.execute_query('test_table', select='id,name', filters={'status': 'active'})
                
                assert result['success'] is True
                assert result['data'] == [{'id': '1', 'name': 'Test'}]
    
    @pytest.mark.asyncio
    async def test_execute_query_no_filters(self):
        """Test execute_query without filters"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = [{'id': '1'}]
        mock_query = Mock()
        mock_query.execute = Mock(return_value=mock_result)
        mock_select = Mock()
        mock_select.select = Mock(return_value=mock_query)
        mock_client.from_ = Mock(return_value=mock_select)
        
        with patch('services.supabase_client.create_client', return_value=mock_client):
            with patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_SERVICE_ROLE_KEY': 'test_key'}):
                manager = SupabaseClientManager()
                result = await manager.execute_query('test_table')
                
                assert result['success'] is True
                mock_query.eq.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_query_exception(self):
        """Test execute_query when client is None"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        with patch.dict(os.environ, {}, clear=True):
            manager = SupabaseClientManager()
            result = await manager.execute_query('test_table')
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_insert_data_success(self):
        """Test successful insert_data"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = [{'id': '1', 'name': 'Test'}]
        mock_insert = Mock()
        mock_insert.execute = Mock(return_value=mock_result)
        mock_table = Mock()
        mock_table.insert = Mock(return_value=mock_insert)
        mock_client.from_ = Mock(return_value=mock_table)
        
        with patch('services.supabase_client.create_client', return_value=mock_client):
            with patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_SERVICE_ROLE_KEY': 'test_key'}):
                manager = SupabaseClientManager()
                result = await manager.insert_data('test_table', {'name': 'Test'})
                
                assert result['success'] is True
                assert result['data'] == [{'id': '1', 'name': 'Test'}]
    
    @pytest.mark.asyncio
    async def test_insert_data_exception(self):
        """Test insert_data when client is None"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        with patch.dict(os.environ, {}, clear=True):
            manager = SupabaseClientManager()
            result = await manager.insert_data('test_table', {'name': 'Test'})
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_update_data_success(self):
        """Test successful update_data"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = [{'id': '1', 'name': 'Updated'}]
        mock_query = Mock()
        mock_query.eq = Mock(return_value=mock_query)
        mock_query.execute = Mock(return_value=mock_result)
        mock_update = Mock()
        mock_update.update = Mock(return_value=mock_query)
        mock_table = Mock()
        mock_table.update = Mock(return_value=mock_query)
        mock_client.from_ = Mock(return_value=mock_table)
        
        with patch('services.supabase_client.create_client', return_value=mock_client):
            with patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_SERVICE_ROLE_KEY': 'test_key'}):
                manager = SupabaseClientManager()
                result = await manager.update_data('test_table', {'name': 'Updated'}, {'id': '1'})
                
                assert result['success'] is True
                assert result['data'] == [{'id': '1', 'name': 'Updated'}]
    
    @pytest.mark.asyncio
    async def test_update_data_exception(self):
        """Test update_data when client is None"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        with patch.dict(os.environ, {}, clear=True):
            manager = SupabaseClientManager()
            result = await manager.update_data('test_table', {'name': 'Updated'}, {'id': '1'})
            
            assert result['success'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_delete_data_success(self):
        """Test successful delete_data"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = [{'id': '1'}]
        mock_query = Mock()
        mock_query.eq = Mock(return_value=mock_query)
        mock_query.execute = Mock(return_value=mock_result)
        mock_delete = Mock()
        mock_delete.delete = Mock(return_value=mock_query)
        mock_table = Mock()
        mock_table.delete = Mock(return_value=mock_query)
        mock_client.from_ = Mock(return_value=mock_table)
        
        with patch('services.supabase_client.create_client', return_value=mock_client):
            with patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_SERVICE_ROLE_KEY': 'test_key'}):
                manager = SupabaseClientManager()
                result = await manager.delete_data('test_table', {'id': '1'})
                
                assert result['success'] is True
                assert result['deleted_count'] == 1
    
    @pytest.mark.asyncio
    async def test_delete_data_no_result(self):
        """Test delete_data when result.data is None"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        mock_client = Mock()
        mock_result = Mock()
        mock_result.data = None
        mock_query = Mock()
        mock_query.eq = Mock(return_value=mock_query)
        mock_query.execute = Mock(return_value=mock_result)
        mock_table = Mock()
        mock_table.delete = Mock(return_value=mock_query)
        mock_client.from_ = Mock(return_value=mock_table)
        
        with patch('services.supabase_client.create_client', return_value=mock_client):
            with patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_SERVICE_ROLE_KEY': 'test_key'}):
                manager = SupabaseClientManager()
                result = await manager.delete_data('test_table', {'id': '1'})
                
                assert result['success'] is True
                assert result['deleted_count'] == 0
    
    @pytest.mark.asyncio
    async def test_delete_data_exception(self):
        """Test delete_data when client is None"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        with patch.dict(os.environ, {}, clear=True):
            manager = SupabaseClientManager()
            result = await manager.delete_data('test_table', {'id': '1'})
            
            assert result['success'] is False
            assert 'error' in result
    
    def test_get_supabase_client_function(self):
        """Test get_supabase_client function"""
        # Clear singleton
        SupabaseClientManager._instance = None
        SupabaseClientManager._client = None
        
        mock_client = Mock()
        with patch('services.supabase_client.create_client', return_value=mock_client):
            with patch.dict(os.environ, {'SUPABASE_URL': 'https://test.supabase.co', 'SUPABASE_SERVICE_ROLE_KEY': 'test_key'}):
                client = get_supabase_client()
                
                assert client is mock_client

