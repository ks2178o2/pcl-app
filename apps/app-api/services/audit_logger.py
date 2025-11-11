# apps/app-api/services/audit_logger.py

"""
Audit Logger Module
Provides a simple singleton interface for audit logging
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .audit_service import AuditService

# Create a singleton instance
_audit_service_instance = None

def get_audit_logger():
    """Get the singleton audit logger instance"""
    global _audit_service_instance
    if _audit_service_instance is None:
        from .audit_service import AuditService
        _audit_service_instance = AuditService()
    return _audit_service_instance

# Create a lazy-loaded module-level instance for easy import
class _LazyAuditLogger:
    """Lazy-loaded proxy for audit logger"""
    def __getattr__(self, name):
        return getattr(get_audit_logger(), name)

audit_logger = _LazyAuditLogger()

