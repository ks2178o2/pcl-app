# apps/app-api/services/audit_service.py

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging
from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class AuditService:
    """Service for managing audit logs"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def create_audit_entry(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new audit log entry"""
        try:
            # Validate required fields
            required_fields = ['user_id', 'organization_id', 'action']
            for field in required_fields:
                if not audit_data.get(field):
                    raise ValueError(f"{field} cannot be empty")
            
            # Add timestamp
            audit_data['created_at'] = datetime.utcnow().isoformat()
            
            # Insert into database
            result = self.supabase.from_('audit_logs').insert(audit_data).execute()
            
            if result.data:
                return {
                    "success": True,
                    "audit_id": result.data[0]['id']
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create audit entry"
                }
                
        except Exception as e:
            logger.error(f"Error creating audit entry: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_audit_logs(self, organization_id: str, limit: int = 100, offset: int = 0, 
                           user_id: Optional[str] = None, action: Optional[str] = None) -> Dict[str, Any]:
        """Get audit logs with optional filtering"""
        try:
            query = self.supabase.from_('audit_logs').select('*')
            query = query.eq('organization_id', organization_id)
            
            if user_id:
                query = query.eq('user_id', user_id)
            if action:
                query = query.eq('action', action)
            
            query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
            
            result = query.execute()
            
            # Get total count
            count_query = self.supabase.from_('audit_logs').select('id', count='exact')
            count_query = count_query.eq('organization_id', organization_id)
            if user_id:
                count_query = count_query.eq('user_id', user_id)
            if action:
                count_query = count_query.eq('action', action)
            
            count_result = count_query.execute()
            total_count = count_result.count if hasattr(count_result, 'count') and count_result.count is not None else 0
            
            return {
                "success": True,
                "logs": result.data or [],
                "total_count": total_count,
                "has_more": offset + len(result.data or []) < total_count if isinstance(total_count, int) else False
            }
            
        except Exception as e:
            logger.error(f"Error getting audit logs: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def filter_audit_logs(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Filter audit logs based on provided criteria"""
        try:
            query = self.supabase.from_('audit_logs').select('*')
            
            # Apply filters
            if 'organization_id' in filters:
                query = query.eq('organization_id', filters['organization_id'])
            if 'user_id' in filters:
                query = query.eq('user_id', filters['user_id'])
            if 'action' in filters:
                query = query.eq('action', filters['action'])
            if 'resource_type' in filters:
                query = query.eq('resource_type', filters['resource_type'])
            if 'start_date' in filters:
                query = query.gte('created_at', filters['start_date'].isoformat())
            if 'end_date' in filters:
                query = query.lte('created_at', filters['end_date'].isoformat())
            
            query = query.order('created_at', desc=True)
            
            result = query.execute()
            
            return {
                "success": True,
                "logs": result.data or []
            }
            
        except Exception as e:
            logger.error(f"Error filtering audit logs: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def export_audit_logs(self, export_config: Dict[str, Any]) -> Dict[str, Any]:
        """Export audit logs in specified format"""
        try:
            # Get logs based on filters
            filters = export_config.get('filters', {})
            logs_result = await self.filter_audit_logs(filters)
            
            if not logs_result['success']:
                return logs_result
            
            logs = logs_result['logs']
            format_type = export_config.get('format', 'json')
            
            if format_type == 'csv':
                # Convert to CSV
                if logs:
                    headers = list(logs[0].keys())
                    csv_data = ','.join(headers) + '\n'
                    for log in logs:
                        row = ','.join(str(log.get(h, '')) for h in headers)
                        csv_data += row + '\n'
                else:
                    csv_data = "No data found"
                
                return {
                    "success": True,
                    "csv_data": csv_data
                }
            
            elif format_type == 'json':
                return {
                    "success": True,
                    "json_data": json.dumps(logs, default=str)
                }
            
            elif format_type == 'xlsx':
                # For now, return mock Excel data
                return {
                    "success": True,
                    "xlsx_data": b"fake_excel_data"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported format: {format_type}"
                }
                
        except Exception as e:
            logger.error(f"Error exporting audit logs: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_audit_statistics(self, organization_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get audit statistics for an organization"""
        try:
            # Get logs in date range
            filters = {
                'organization_id': organization_id,
                'start_date': start_date,
                'end_date': end_date
            }
            
            logs_result = await self.filter_audit_logs(filters)
            
            if not logs_result['success']:
                return logs_result
            
            logs = logs_result['logs']
            
            # Calculate statistics
            action_counts = {}
            unique_users = set()
            
            for log in logs:
                action = log.get('action', 'unknown')
                action_counts[action] = action_counts.get(action, 0) + 1
                unique_users.add(log.get('user_id'))
            
            return {
                "success": True,
                "statistics": {
                    "action_counts": action_counts,
                    "total_actions": len(logs),
                    "unique_users": len(unique_users)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting audit statistics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_user_activity_summary(self, organization_id: str, user_id: str) -> Dict[str, Any]:
        """Get activity summary for a specific user"""
        try:
            filters = {
                'organization_id': organization_id,
                'user_id': user_id
            }
            
            logs_result = await self.filter_audit_logs(filters)
            
            if not logs_result['success']:
                return logs_result
            
            logs = logs_result['logs']
            
            if not logs:
                return {
                    "success": True,
                    "summary": {
                        "user_id": user_id,
                        "action_count": 0,
                        "last_activity": None,
                        "most_common_action": None,
                        "active_days": 0
                    }
                }
            
            # Calculate summary
            action_counts = {}
            active_days = set()
            
            for log in logs:
                action = log.get('action', 'unknown')
                action_counts[action] = action_counts.get(action, 0) + 1
                
                # Extract date from timestamp
                created_at = log.get('created_at', '')
                if created_at:
                    date_str = created_at.split('T')[0]
                    active_days.add(date_str)
            
            most_common_action = max(action_counts.items(), key=lambda x: x[1])[0] if action_counts else None
            last_activity = logs[0].get('created_at') if logs else None
            
            return {
                "success": True,
                "summary": {
                    "user_id": user_id,
                    "action_count": len(logs),
                    "last_activity": last_activity,
                    "most_common_action": most_common_action,
                    "active_days": len(active_days)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user activity summary: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_security_alerts(self, organization_id: str, time_window_minutes: int = 5) -> Dict[str, Any]:
        """Check for security-related alerts"""
        try:
            # Get recent logs
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=time_window_minutes)
            
            filters = {
                'organization_id': organization_id,
                'start_date': start_time,
                'end_date': end_time
            }
            
            logs_result = await self.filter_audit_logs(filters)
            
            if not logs_result['success']:
                return logs_result
            
            logs = logs_result['logs']
            
            # Check for suspicious patterns
            alerts = []
            
            # Check for multiple failed logins
            failed_logins = [log for log in logs if log.get('action') == 'login_failed']
            if len(failed_logins) >= 3:
                alerts.append({
                    "alert_type": "multiple_failed_logins",
                    "user_id": failed_logins[0].get('user_id'),
                    "count": len(failed_logins),
                    "time_window": f"{time_window_minutes} minutes",
                    "severity": "high"
                })
            
            return {
                "success": True,
                "alerts": alerts
            }
            
        except Exception as e:
            logger.error(f"Error checking security alerts: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup_old_logs(self, organization_id: str, retention_days: int = 90) -> Dict[str, Any]:
        """Clean up old audit logs"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Delete old logs
            result = self.supabase.from_('audit_logs').delete().eq('organization_id', organization_id).lt('created_at', cutoff_date.isoformat()).execute()
            
            deleted_count = len(result.data) if result.data else 0
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "retention_days": retention_days
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_performance_metrics(self, organization_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get performance metrics for audit operations"""
        try:
            # Mock performance data for now
            metrics = {
                "rag_query": {
                    "avg_response_time": 150.5,
                    "max_response_time": 500,
                    "min_response_time": 50,
                    "total_requests": 1000
                }
            }
            
            return {
                "success": True,
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
