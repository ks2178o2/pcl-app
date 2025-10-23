# apps/app-api/services/enhanced_context_manager.py

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json
import logging
import csv
import io
from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class EnhancedContextManager:
    """Enhanced service for managing RAG context items with app-wide capabilities"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    # ==================== APP-WIDE CONTEXT MANAGEMENT ====================
    
    async def add_global_context_item(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new global context item accessible to all tenants"""
        try:
            # Validate required fields
            required_fields = ['rag_feature', 'item_id', 'item_type', 'item_title', 'item_content']
            for field in required_fields:
                if not context_data.get(field):
                    raise ValueError(f"{field} cannot be empty")
            
            # Validate confidence score
            confidence_score = context_data.get('confidence_score', 0.5)
            if not (0 <= confidence_score <= 1):
                raise ValueError("Confidence score must be between 0 and 1")
            
            # Add metadata
            context_data['created_at'] = datetime.utcnow().isoformat()
            context_data['status'] = context_data.get('status', 'active')
            context_data['priority'] = context_data.get('priority', 1)
            context_data['tags'] = context_data.get('tags', [])
            
            # Check for duplicates globally
            existing = await self._check_global_duplicate_item(context_data['item_id'])
            if existing:
                return {
                    "success": False,
                    "error": "Global item already exists"
                }
            
            # Insert into global_context_items table
            result = self.supabase.from_('global_context_items').insert(context_data).execute()
            
            if result.data:
                return {
                    "success": True,
                    "item_id": result.data[0]['id'],
                    "scope": "global"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create global context item"
                }
                
        except Exception as e:
            logger.error(f"Error adding global context item: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_global_context_items(self, rag_feature: Optional[str] = None, 
                                     organization_id: Optional[str] = None,
                                     limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get global context items accessible to a tenant"""
        try:
            query = self.supabase.from_('global_context_items').select('*', count='exact')
            
            # Filter by RAG feature if specified
            if rag_feature:
                query = query.eq('rag_feature', rag_feature)
            
            # Filter by status
            query = query.eq('status', 'active')
            
            # Check if organization has access to this RAG feature
            if organization_id and rag_feature:
                access_check = self.supabase.from_('tenant_context_access').select('enabled').eq('organization_id', organization_id).eq('rag_feature', rag_feature).eq('enabled', True).execute()
                if not access_check.data:
                    return {
                        "success": True,
                        "items": [],
                        "total_count": 0,
                        "has_more": False,
                        "message": "No access to this RAG feature"
                    }
            
            # Apply pagination
            query = query.order('priority', desc=True).order('created_at', desc=True).range(offset, offset + limit - 1)
            
            result = query.execute()
            
            return {
                "success": True,
                "items": result.data or [],
                "total_count": result.count if hasattr(result, 'count') and result.count is not None else 0,
                "has_more": offset + len(result.data or []) < (result.count if hasattr(result, 'count') and result.count is not None else 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting global context items: {e}")
            return {
                "success": False,
                "error": str(e),
                "items": [],
                "total_count": 0,
                "has_more": False
            }
    
    # ==================== TENANT ACCESS MANAGEMENT ====================
    
    async def grant_tenant_access(self, organization_id: str, rag_feature: str, 
                                access_level: str = 'read') -> Dict[str, Any]:
        """Grant a tenant access to a global RAG feature"""
        try:
            # Check if access already exists
            existing = self.supabase.from_('tenant_context_access').select('*').eq('organization_id', organization_id).eq('rag_feature', rag_feature).execute()
            
            if existing.data:
                # Update existing access
                result = self.supabase.from_('tenant_context_access').update({
                    'access_level': access_level,
                    'enabled': True,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('organization_id', organization_id).eq('rag_feature', rag_feature).execute()
            else:
                # Create new access
                result = self.supabase.from_('tenant_context_access').insert({
                    'organization_id': organization_id,
                    'rag_feature': rag_feature,
                    'access_level': access_level,
                    'enabled': True
                }).execute()
            
            if result.data:
                return {
                    "success": True,
                    "access_id": result.data[0]['id']
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to grant tenant access"
                }
                
        except Exception as e:
            logger.error(f"Error granting tenant access: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def revoke_tenant_access(self, organization_id: str, rag_feature: str) -> Dict[str, Any]:
        """Revoke a tenant's access to a global RAG feature"""
        try:
            result = self.supabase.from_('tenant_context_access').update({
                'enabled': False,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('organization_id', organization_id).eq('rag_feature', rag_feature).execute()
            
            if result.data:
                return {
                    "success": True,
                    "revoked_id": result.data[0]['id']
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to revoke tenant access"
                }
                
        except Exception as e:
            logger.error(f"Error revoking tenant access: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== CROSS-TENANT KNOWLEDGE SHARING ====================
    
    async def share_context_item(self, source_org_id: str, target_org_id: str, 
                               rag_feature: str, item_id: str, shared_by: str,
                               sharing_type: str = 'read_only') -> Dict[str, Any]:
        """Share a context item between tenants"""
        try:
            # Check if sharing already exists
            existing = self.supabase.from_('context_sharing').select('*').eq('source_organization_id', source_org_id).eq('target_organization_id', target_org_id).eq('rag_feature', rag_feature).eq('item_id', item_id).execute()
            
            if existing.data:
                return {
                    "success": False,
                    "error": "Sharing already exists"
                }
            
            # Create sharing request
            result = self.supabase.from_('context_sharing').insert({
                'source_organization_id': source_org_id,
                'target_organization_id': target_org_id,
                'rag_feature': rag_feature,
                'item_id': item_id,
                'sharing_type': sharing_type,
                'status': 'pending',
                'shared_by': shared_by
            }).execute()
            
            if result.data:
                return {
                    "success": True,
                    "sharing_id": result.data[0]['id']
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create sharing request"
                }
                
        except Exception as e:
            logger.error(f"Error sharing context item: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def approve_sharing_request(self, sharing_id: str, approved_by: str) -> Dict[str, Any]:
        """Approve a context sharing request"""
        try:
            result = self.supabase.from_('context_sharing').update({
                'status': 'approved',
                'approved_by': approved_by,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', sharing_id).execute()
            
            if result.data:
                return {
                    "success": True,
                    "approved_id": result.data[0]['id']
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to approve sharing request"
                }
                
        except Exception as e:
            logger.error(f"Error approving sharing request: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_shared_context_items(self, organization_id: str, 
                                     rag_feature: Optional[str] = None) -> Dict[str, Any]:
        """Get context items shared with an organization"""
        try:
            query = self.supabase.from_('context_sharing').select('*')
            query = query.eq('target_organization_id', organization_id)
            query = query.eq('status', 'approved')
            
            if rag_feature:
                query = query.eq('rag_feature', rag_feature)
            
            result = query.execute()
            
            return {
                "success": True,
                "shared_items": result.data or []
            }
            
        except Exception as e:
            logger.error(f"Error getting shared context items: {e}")
            return {
                "success": False,
                "error": str(e),
                "shared_items": []
            }
    
    # ==================== ENHANCED UPLOAD MECHANISMS ====================
    
    async def upload_file_content(self, file_content: str, file_type: str, 
                                organization_id: str, rag_feature: str,
                                uploaded_by: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Upload and process file content (PDF, DOCX, TXT, etc.)"""
        try:
            # This would integrate with file processing libraries
            # For now, we'll create a basic implementation
            
            processed_items = []
            success_count = 0
            error_count = 0
            sections = []
            
            # Basic text processing (in production, use proper file parsers)
            if file_type.lower() in ['txt', 'md']:
                # Split by paragraphs or sections
                sections = file_content.split('\n\n')
                for i, section in enumerate(sections):
                    if section.strip():
                        item_data = {
                            'organization_id': organization_id,
                            'rag_feature': rag_feature,
                            'item_id': f"file-upload-{int(datetime.utcnow().timestamp())}-{i}",
                            'item_type': 'document_section',
                            'item_title': f"Section {i+1}",
                            'item_content': section.strip(),
                            'source': f"file_upload_{file_type}",
                            'confidence_score': 0.8
                        }
                        
                        # Add to tenant context
                        result = await self.add_context_item(item_data)
                        if result['success']:
                            success_count += 1
                            processed_items.append(result['item_id'])
                        else:
                            error_count += 1
            
            # Log the upload
            await self._log_upload(organization_id, 'file', rag_feature, 
                                 len(sections), success_count, error_count, 
                                 f"file_upload_{file_type}", uploaded_by)
            
            return {
                "success": True,
                "processed_items": processed_items,
                "success_count": success_count,
                "error_count": error_count,
                "upload_type": "file"
            }
            
        except Exception as e:
            logger.error(f"Error uploading file content: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def scrape_web_content(self, url: str, organization_id: str, 
                               rag_feature: str, uploaded_by: str) -> Dict[str, Any]:
        """Scrape web content and add to context"""
        try:
            # This would integrate with web scraping libraries
            # For now, we'll create a basic implementation
            
            # In production, use libraries like BeautifulSoup, Scrapy, etc.
            # For demo purposes, we'll simulate web scraping
            
            scraped_content = f"Content scraped from {url} at {datetime.utcnow().isoformat()}"
            
            item_data = {
                'organization_id': organization_id,
                'rag_feature': rag_feature,
                'item_id': f"web-scrape-{int(datetime.utcnow().timestamp())}",
                'item_type': 'web_content',
                'item_title': f"Web Content from {url}",
                'item_content': scraped_content,
                'source': url,
                'confidence_score': 0.7
            }
            
            result = await self.add_context_item(item_data)
            
            # Log the upload
            await self._log_upload(organization_id, 'web_scrape', rag_feature, 
                                 1, 1 if result['success'] else 0, 
                                 0 if result['success'] else 1, url, uploaded_by)
            
            return {
                "success": result['success'],
                "scraped_item": result.get('item_id'),
                "url": url,
                "upload_type": "web_scrape"
            }
            
        except Exception as e:
            logger.error(f"Error scraping web content: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def bulk_api_upload(self, items: List[Dict[str, Any]], 
                            organization_id: str, rag_feature: str,
                            uploaded_by: str) -> Dict[str, Any]:
        """Bulk upload via API"""
        try:
            success_count = 0
            error_count = 0
            processed_items = []
            
            for item in items:
                # Add organization and feature context
                item['organization_id'] = organization_id
                item['rag_feature'] = rag_feature
                
                result = await self.add_context_item(item)
                if result['success']:
                    success_count += 1
                    processed_items.append(result['item_id'])
                else:
                    error_count += 1
            
            # Log the upload
            await self._log_upload(organization_id, 'api', rag_feature, 
                                 len(items), success_count, error_count, 
                                 "bulk_api_upload", uploaded_by)
            
            return {
                "success": True,
                "processed_items": processed_items,
                "success_count": success_count,
                "error_count": error_count,
                "upload_type": "bulk_api"
            }
            
        except Exception as e:
            logger.error(f"Error in bulk API upload: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== QUOTA MANAGEMENT ====================
    
    async def get_organization_quotas(self, organization_id: str) -> Dict[str, Any]:
        """Get organization's context quotas and usage"""
        try:
            result = self.supabase.from_('organization_context_quotas').select('*').eq('organization_id', organization_id).single().execute()
            
            if result.data:
                return {
                    "success": True,
                    "quotas": result.data
                }
            else:
                # Create default quotas if they don't exist
                default_quotas = {
                    'organization_id': organization_id,
                    'max_context_items': 1000,
                    'max_global_access_features': 10,
                    'max_sharing_requests': 50,
                    'current_context_items': 0,
                    'current_global_access': 0,
                    'current_sharing_requests': 0
                }
                
                create_result = self.supabase.from_('organization_context_quotas').insert(default_quotas).execute()
                
                return {
                    "success": True,
                    "quotas": create_result.data[0] if create_result.data else default_quotas
                }
                
        except Exception as e:
            logger.error(f"Error getting organization quotas: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_organization_quotas(self, organization_id: str, 
                                      quota_updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update organization's context quotas"""
        try:
            quota_updates['updated_at'] = datetime.utcnow().isoformat()
            
            result = self.supabase.from_('organization_context_quotas').update(quota_updates).eq('organization_id', organization_id).execute()
            
            if result.data:
                return {
                    "success": True,
                    "updated_quotas": result.data[0]
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to update quotas"
                }
                
        except Exception as e:
            logger.error(f"Error updating organization quotas: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== HELPER METHODS ====================
    
    async def _check_global_duplicate_item(self, item_id: str) -> bool:
        """Check if a global item already exists"""
        try:
            result = self.supabase.from_('global_context_items').select('id').eq('item_id', item_id).execute()
            return len(result.data or []) > 0
        except:
            return False
    
    async def _log_upload(self, organization_id: str, upload_type: str, 
                        rag_feature: str, items_count: int, success_count: int,
                        error_count: int, upload_source: str, uploaded_by: str):
        """Log upload activity"""
        try:
            log_data = {
                'organization_id': organization_id,
                'upload_type': upload_type,
                'rag_feature': rag_feature,
                'items_count': items_count,
                'success_count': success_count,
                'error_count': error_count,
                'upload_source': upload_source,
                'uploaded_by': uploaded_by
            }
            
            self.supabase.from_('context_upload_logs').insert(log_data).execute()
        except Exception as e:
            logger.error(f"Error logging upload: {e}")
    
    # ==================== LEGACY COMPATIBILITY ====================
    
    async def add_context_item(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method for backward compatibility"""
        # This would call the original ContextManager method
        # For now, we'll implement a basic version
        try:
            required_fields = ['organization_id', 'rag_feature', 'item_id', 'item_type', 'item_title', 'item_content']
            for field in required_fields:
                if not context_data.get(field):
                    raise ValueError(f"{field} cannot be empty")
            
            context_data['created_at'] = datetime.utcnow().isoformat()
            context_data['status'] = context_data.get('status', 'included')
            context_data['priority'] = context_data.get('priority', 1)
            
            result = self.supabase.from_('rag_context_items').insert(context_data).execute()
            
            if result.data:
                return {
                    "success": True,
                    "item_id": result.data[0]['id']
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create context item"
                }
                
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== HIERARCHY SUPPORT ====================
    
    async def share_to_children(self, source_org_id: str, item_id: str, rag_feature: str, shared_by: str) -> Dict[str, Any]:
        """Share context item to all child organizations"""
        try:
            # Get all child organizations
            children_result = self.supabase.from_('organizations').select('id').eq('parent_organization_id', source_org_id).execute()
            
            if not children_result.data:
                return {
                    "success": True,
                    "message": "No child organizations found",
                    "shared_count": 0
                }
            
            # Create sharing requests for each child
            sharing_requests = []
            for child in children_result.data:
                sharing_requests.append({
                    'source_organization_id': source_org_id,
                    'target_organization_id': child['id'],
                    'rag_feature': rag_feature,
                    'item_id': item_id,
                    'sharing_type': 'hierarchy_down',
                    'status': 'pending',
                    'shared_by': shared_by
                })
            
            # Insert all sharing requests
            result = self.supabase.from_('context_sharing').insert(sharing_requests).execute()
            
            if result.data:
                return {
                    "success": True,
                    "shared_count": len(result.data),
                    "message": f"Shared to {len(result.data)} child organizations"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create sharing requests"
                }
                
        except Exception as e:
            logger.error(f"Error sharing to children: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def share_to_parent(self, source_org_id: str, item_id: str, rag_feature: str, shared_by: str) -> Dict[str, Any]:
        """Share context item to parent organization"""
        try:
            # Get parent organization
            org_result = self.supabase.from_('organizations').select('parent_organization_id').eq('id', source_org_id).execute()
            
            if not org_result.data or not org_result.data[0].get('parent_organization_id'):
                return {
                    "success": False,
                    "error": "No parent organization found"
                }
            
            parent_id = org_result.data[0]['parent_organization_id']
            
            # Create sharing request
            result = self.supabase.from_('context_sharing').insert({
                'source_organization_id': source_org_id,
                'target_organization_id': parent_id,
                'rag_feature': rag_feature,
                'item_id': item_id,
                'sharing_type': 'hierarchy_up',
                'status': 'pending',
                'shared_by': shared_by
            }).execute()
            
            if result.data:
                return {
                    "success": True,
                    "sharing_id": result.data[0]['id'],
                    "message": "Shared to parent organization"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create sharing request"
                }
                
        except Exception as e:
            logger.error(f"Error sharing to parent: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_pending_approvals(self, organization_id: str) -> Dict[str, Any]:
        """Get pending sharing requests for an organization"""
        try:
            result = self.supabase.from_('context_sharing').select('*').eq('target_organization_id', organization_id).eq('status', 'pending').execute()
            
            if result.data:
                return {
                    "success": True,
                    "pending_requests": result.data,
                    "count": len(result.data)
                }
            else:
                return {
                    "success": True,
                    "pending_requests": [],
                    "count": 0
                }
                
        except Exception as e:
            logger.error(f"Error getting pending approvals: {e}")
            return {
                "success": False,
                "error": str(e),
                "pending_requests": []
            }
    
    async def approve_shared_item(self, sharing_id: str, approved_by: str) -> Dict[str, Any]:
        """Approve a shared context item"""
        try:
            # Update sharing status
            result = self.supabase.from_('context_sharing').update({
                'status': 'approved',
                'approved_by': approved_by,
                'approved_at': datetime.utcnow().isoformat()
            }).eq('id', sharing_id).execute()
            
            if result.data:
                # Get the sharing details
                sharing_data = result.data[0]
                
                # Copy the context item to the target organization
                item_result = self.supabase.from_('context_items').select('*').eq('id', sharing_data['item_id']).execute()
                
                if item_result.data:
                    original_item = item_result.data[0]
                    
                    # Create new item in target organization
                    new_item = {
                        'organization_id': sharing_data['target_organization_id'],
                        'rag_feature': sharing_data['rag_feature'],
                        'title': original_item['title'],
                        'content': original_item['content'],
                        'item_type': original_item['item_type'],
                        'status': 'active',
                        'source_type': 'shared',
                        'source_organization_id': sharing_data['source_organization_id'],
                        'shared_item_id': sharing_data['item_id']
                    }
                    
                    insert_result = self.supabase.from_('context_items').insert(new_item).execute()
                    
                    if insert_result.data:
                        return {
                            "success": True,
                            "approved_id": sharing_id,
                            "new_item_id": insert_result.data[0]['id'],
                            "message": "Item approved and copied to organization"
                        }
                    else:
                        return {
                            "success": False,
                            "error": "Failed to copy item to target organization"
                        }
                else:
                    return {
                        "success": False,
                        "error": "Original item not found"
                    }
            else:
                return {
                    "success": False,
                    "error": "Failed to approve sharing request"
                }
                
        except Exception as e:
            logger.error(f"Error approving shared item: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def reject_shared_item(self, sharing_id: str, rejected_by: str, reason: str = None) -> Dict[str, Any]:
        """Reject a shared context item"""
        try:
            result = self.supabase.from_('context_sharing').update({
                'status': 'rejected',
                'rejected_by': rejected_by,
                'rejected_at': datetime.utcnow().isoformat(),
                'rejection_reason': reason
            }).eq('id', sharing_id).execute()
            
            if result.data:
                return {
                    "success": True,
                    "rejected_id": sharing_id,
                    "message": "Sharing request rejected"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to reject sharing request"
                }
                
        except Exception as e:
            logger.error(f"Error rejecting shared item: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_hierarchy_sharing_stats(self, organization_id: str) -> Dict[str, Any]:
        """Get sharing statistics for hierarchy"""
        try:
            # Get outgoing shares (to children)
            outgoing_result = self.supabase.from_('context_sharing').select('count', count='exact').eq('source_organization_id', organization_id).eq('sharing_type', 'hierarchy_down').execute()
            
            # Get incoming shares (from parent)
            incoming_result = self.supabase.from_('context_sharing').select('count', count='exact').eq('target_organization_id', organization_id).eq('sharing_type', 'hierarchy_up').execute()
            
            # Get pending approvals
            pending_result = self.supabase.from_('context_sharing').select('count', count='exact').eq('target_organization_id', organization_id).eq('status', 'pending').execute()
            
            return {
                "success": True,
                "stats": {
                    "outgoing_shares": outgoing_result.count if outgoing_result.count else 0,
                    "incoming_shares": incoming_result.count if incoming_result.count else 0,
                    "pending_approvals": pending_result.count if pending_result.count else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting hierarchy sharing stats: {e}")
            return {
                "success": False,
                "error": str(e),
                "stats": {
                    "outgoing_shares": 0,
                    "incoming_shares": 0,
                    "pending_approvals": 0
                }
            }
