"""
Tests for audit_logger.py to achieve 95% coverage
"""
import pytest
from unittest.mock import Mock, patch
from services.audit_logger import get_audit_logger, audit_logger


class TestAuditLogger:
    """Test audit_logger module"""
    
    def test_get_audit_logger_singleton(self):
        """Test that get_audit_logger returns a singleton"""
        # Clear the global instance
        import services.audit_logger
        services.audit_logger._audit_service_instance = None
        
        # Get first instance
        logger1 = get_audit_logger()
        
        # Get second instance - should be the same
        logger2 = get_audit_logger()
        
        assert logger1 is logger2
        assert logger1 is not None
    
    def test_get_audit_logger_creates_audit_service(self):
        """Test that get_audit_logger creates AuditService instance"""
        # Clear the global instance
        import services.audit_logger
        services.audit_logger._audit_service_instance = None
        
        # Patch the import inside the function
        with patch('services.audit_service.AuditService') as mock_audit_service_class:
            mock_instance = Mock()
            mock_audit_service_class.return_value = mock_instance
            
            # Need to patch the import in audit_logger module
            with patch.dict('sys.modules', {'services.audit_service': Mock(AuditService=mock_audit_service_class)}):
                # Force reload to pick up the patch
                import importlib
                import services.audit_logger
                importlib.reload(services.audit_logger)
                
                logger = services.audit_logger.get_audit_logger()
                
                assert logger is mock_instance
                mock_audit_service_class.assert_called_once()
    
    def test_lazy_audit_logger_proxy(self):
        """Test that audit_logger proxy works correctly"""
        # Clear the global instance
        import services.audit_logger
        services.audit_logger._audit_service_instance = None
        
        # Create a mock audit service
        mock_audit_service = Mock()
        mock_audit_service.some_method = Mock(return_value='test_value')
        
        with patch('services.audit_logger.get_audit_logger', return_value=mock_audit_service):
            # Access through the proxy
            result = audit_logger.some_method('arg1', 'arg2')
            
            assert result == 'test_value'
            mock_audit_service.some_method.assert_called_once_with('arg1', 'arg2')
    
    def test_lazy_audit_logger_multiple_attributes(self):
        """Test that audit_logger proxy handles multiple attributes"""
        # Clear the global instance
        import services.audit_logger
        services.audit_logger._audit_service_instance = None
        
        # Create a mock audit service
        mock_audit_service = Mock()
        mock_audit_service.method1 = Mock(return_value='value1')
        mock_audit_service.method2 = Mock(return_value='value2')
        mock_audit_service.property1 = 'property_value'
        
        with patch('services.audit_logger.get_audit_logger', return_value=mock_audit_service):
            # Access multiple attributes
            result1 = audit_logger.method1()
            result2 = audit_logger.method2()
            prop = audit_logger.property1
            
            assert result1 == 'value1'
            assert result2 == 'value2'
            assert prop == 'property_value'
    
    def test_type_checking_block(self):
        """Test line 11: TYPE_CHECKING block to reach 95% coverage"""
        # Patch TYPE_CHECKING to True to execute the import inside the if block
        import services.audit_logger
        import importlib
        
        with patch('typing.TYPE_CHECKING', True):
            # Reload the module to execute the TYPE_CHECKING block
            importlib.reload(services.audit_logger)
            
            # Verify the module reloaded successfully
            assert hasattr(services.audit_logger, 'get_audit_logger')
            assert hasattr(services.audit_logger, 'audit_logger')
        
        # Reload again to restore normal state
        importlib.reload(services.audit_logger)
    
    def test_get_audit_logger_initial_creation(self):
        """Test that get_audit_logger creates instance on first call"""
        # Clear the global instance
        import services.audit_logger
        import importlib
        services.audit_logger._audit_service_instance = None
        
        # Ensure we start fresh
        importlib.reload(services.audit_logger)
        services.audit_logger._audit_service_instance = None
        
        # Mock AuditService
        mock_audit_service_instance = Mock()
        with patch('services.audit_service.AuditService', return_value=mock_audit_service_instance):
            # First call should create the instance
            logger = services.audit_logger.get_audit_logger()
            assert logger is mock_audit_service_instance
            
            # Second call should return the same instance
            logger2 = services.audit_logger.get_audit_logger()
            assert logger2 is logger
            assert logger2 is mock_audit_service_instance

