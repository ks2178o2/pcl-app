# apps/app-api/services/context_manager.py

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging
from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class ContextManager:
    """Service for managing RAG context items"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def add_context_item(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new context item"""
        try:
            # Validate required fields
            required_fields = ['organization_id', 'rag_feature', 'item_id', 'item_type', 'item_title', 'item_content']
            for field in required_fields:
                if not context_data.get(field):
                    raise ValueError(f"{field} cannot be empty")
            
            # Validate confidence score
            confidence_score = context_data.get('confidence_score', 0.5)
            if not (0 <= confidence_score <= 1):
                raise ValueError("Confidence score must be between 0 and 1")
            
            # Add metadata
            context_data['created_at'] = datetime.utcnow().isoformat()
            context_data['status'] = context_data.get('status', 'included')
            context_data['priority'] = context_data.get('priority', 1)
            
            # Check for duplicates
            existing = await self._check_duplicate_item(
                context_data['organization_id'],
                context_data['rag_feature'],
                context_data['item_id']
            )
            
            if existing:
                return {
                    "success": False,
                    "error": "Item already exists"
                }
            
            # Insert into database
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
                
        except Exception as e:
            logger.error(f"Error adding context item: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def remove_context_item(self, organization_id: str, rag_feature: str, item_id: str, 
                                reason: str, removed_by: str) -> Dict[str, Any]:
        """Remove a context item"""
        try:
            # Check if item exists
            existing = await self._get_context_item(organization_id, rag_feature, item_id)
            if not existing:
                return {
                    "success": False,
                    "error": "Item not found"
                }
            
            # Delete from database
            result = self.supabase.from_('rag_context_items').delete().eq('organization_id', organization_id).eq('rag_feature', rag_feature).eq('item_id', item_id).execute()
            
            if result.data:
                return {
                    "success": True,
                    "removed_id": result.data[0]['id']
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to remove context item"
                }
                
        except Exception as e:
            logger.error(f"Error removing context item: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_context_status(self, organization_id: str, rag_feature: str, item_id: str,
                                  new_status: str, reason: str, updated_by: str) -> Dict[str, Any]:
        """Update the status of a context item"""
        try:
            # Check if item exists
            existing = await self._get_context_item(organization_id, rag_feature, item_id)
            if not existing:
                return {
                    "success": False,
                    "error": "Item not found"
                }
            
            # Update status
            update_data = {
                'status': new_status,
                'updated_at': datetime.utcnow().isoformat(),
                'updated_by': updated_by,
                'update_reason': reason
            }
            
            result = self.supabase.from_('rag_context_items').update(update_data).eq('organization_id', organization_id).eq('rag_feature', rag_feature).eq('item_id', item_id).execute()
            
            if result.data:
                return {
                    "success": True,
                    "updated_id": result.data[0]['id']
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to update context item"
                }
                
        except Exception as e:
            logger.error(f"Error updating context status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_context_items(self, organization_id: str, rag_feature: Optional[str] = None,
                              filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get context items with optional filtering"""
        try:
            query = self.supabase.from_('rag_context_items').select('*')
            query = query.eq('organization_id', organization_id)
            
            if rag_feature:
                query = query.eq('rag_feature', rag_feature)
            
            # Apply additional filters
            if filters:
                if 'status' in filters:
                    query = query.eq('status', filters['status'])
                if 'item_types' in filters:
                    query = query.in_('item_type', filters['item_types'])
                if 'min_confidence' in filters:
                    query = query.gte('confidence_score', filters['min_confidence'])
                if 'max_priority' in filters:
                    query = query.lte('priority', filters['max_priority'])
            
            query = query.order('created_at', desc=True)
            
            result = query.execute()
            
            return {
                "success": True,
                "items": result.data or []
            }
            
        except Exception as e:
            logger.error(f"Error getting context items: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def filter_context_by_feature(self, organization_id: str, rag_feature: str) -> Dict[str, Any]:
        """Filter context items by RAG feature"""
        return await self.get_context_items(organization_id, rag_feature)
    
    async def filter_context_by_item_type(self, organization_id: str, item_types: List[str]) -> Dict[str, Any]:
        """Filter context items by item type"""
        filters = {'item_types': item_types}
        return await self.get_context_items(organization_id, filters=filters)
    
    async def filter_context_by_confidence(self, organization_id: str, min_confidence: float, max_confidence: float) -> Dict[str, Any]:
        """Filter context items by confidence score"""
        filters = {
            'min_confidence': min_confidence,
            'max_confidence': max_confidence
        }
        return await self.get_context_items(organization_id, filters=filters)
    
    async def filter_context_by_priority(self, organization_id: str, min_priority: int, max_priority: int) -> Dict[str, Any]:
        """Filter context items by priority"""
        filters = {
            'min_priority': min_priority,
            'max_priority': max_priority
        }
        return await self.get_context_items(organization_id, filters=filters)
    
    async def get_context_statistics(self, organization_id: str) -> Dict[str, Any]:
        """Get context statistics for an organization"""
        try:
            # Get all context items for the organization
            result = self.supabase.from_('rag_context_items').select('rag_feature, confidence_score').eq('organization_id', organization_id).execute()
            
            items = result.data or []
            
            # Calculate statistics
            feature_counts = {}
            total_confidence = 0
            
            for item in items:
                feature = item.get('rag_feature', 'unknown')
                feature_counts[feature] = feature_counts.get(feature, 0) + 1
                total_confidence += item.get('confidence_score', 0)
            
            avg_confidence = total_confidence / len(items) if items else 0
            
            return {
                "success": True,
                "statistics": {
                    "feature_counts": feature_counts,
                    "total_items": len(items),
                    "avg_confidence": round(avg_confidence, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting context statistics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def bulk_update_context_items(self, organization_id: str, rag_feature: str, 
                                      updates: List[Dict[str, Any]], updated_by: str) -> Dict[str, Any]:
        """Bulk update context items"""
        try:
            updated_count = 0
            
            for update in updates:
                item_id = update.get('item_id')
                if not item_id:
                    continue
                
                update_data = {
                    'status': update.get('status'),
                    'updated_at': datetime.utcnow().isoformat(),
                    'updated_by': updated_by,
                    'update_reason': update.get('reason', 'Bulk update')
                }
                
                # Remove None values
                update_data = {k: v for k, v in update_data.items() if v is not None}
                
                result = self.supabase.from_('rag_context_items').update(update_data).eq('organization_id', organization_id).eq('rag_feature', rag_feature).eq('item_id', item_id).execute()
                
                if result.data:
                    updated_count += 1
            
            return {
                "success": True,
                "updated_count": updated_count
            }
            
        except Exception as e:
            logger.error(f"Error bulk updating context items: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_context_items(self, organization_id: str, search_query: str, 
                                 rag_feature: Optional[str] = None) -> Dict[str, Any]:
        """Search context items by content"""
        try:
            query = self.supabase.from_('rag_context_items').select('*')
            query = query.eq('organization_id', organization_id)
            
            if rag_feature:
                query = query.eq('rag_feature', rag_feature)
            
            # Search in title and content
            query = query.or_(f"item_title.ilike.%{search_query}%,item_content.ilike.%{search_query}%")
            
            result = query.execute()
            
            return {
                "success": True,
                "items": result.data or []
            }
            
        except Exception as e:
            logger.error(f"Error searching context items: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def export_context_items(self, export_config: Dict[str, Any]) -> Dict[str, Any]:
        """Export context items"""
        try:
            organization_id = export_config['organization_id']
            rag_feature = export_config.get('rag_feature')
            format_type = export_config.get('format', 'csv')
            
            # Get items
            items_result = await self.get_context_items(organization_id, rag_feature)
            
            if not items_result['success']:
                return items_result
            
            items = items_result['items']
            
            if format_type == 'csv':
                if items:
                    headers = ['id', 'title', 'content']
                    csv_data = ','.join(headers) + '\n'
                    for item in items:
                        row = f"{item.get('id', '')},{item.get('item_title', '')},{item.get('item_content', '')}"
                        csv_data += row + '\n'
                else:
                    csv_data = "No data found"
                
                return {
                    "success": True,
                    "csv_data": csv_data
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unsupported format: {format_type}"
                }
                
        except Exception as e:
            logger.error(f"Error exporting context items: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def import_context_items(self, organization_id: str, rag_feature: str, 
                                 items: List[Dict[str, Any]], imported_by: str) -> Dict[str, Any]:
        """Import context items"""
        try:
            imported_count = 0
            
            for item_data in items:
                item_data['organization_id'] = organization_id
                item_data['rag_feature'] = rag_feature
                item_data['added_by'] = imported_by
                
                result = await self.add_context_item(item_data)
                if result['success']:
                    imported_count += 1
            
            return {
                "success": True,
                "imported_count": imported_count
            }
            
        except Exception as e:
            logger.error(f"Error importing context items: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_duplicate_items(self, organization_id: str, rag_feature: str, 
                                 item_ids: List[str]) -> Dict[str, Any]:
        """Check for duplicate items"""
        try:
            result = self.supabase.from_('rag_context_items').select('id, item_id, item_title').eq('organization_id', organization_id).eq('rag_feature', rag_feature).in_('item_id', item_ids).execute()
            
            return {
                "success": True,
                "duplicates": result.data or []
            }
            
        except Exception as e:
            logger.error(f"Error checking duplicate items: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_performance_metrics(self, organization_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get performance metrics for context operations"""
        try:
            # Mock performance data for now
            metrics = {
                "best_practice_kb": {
                    "avg_query_time": 150.5,
                    "total_queries": 1000,
                    "hit_rate": 0.85
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
    
    async def _check_duplicate_item(self, organization_id: str, rag_feature: str, item_id: str) -> bool:
        """Check if an item already exists"""
        try:
            result = self.supabase.from_('rag_context_items').select('id').eq('organization_id', organization_id).eq('rag_feature', rag_feature).eq('item_id', item_id).execute()
            return len(result.data or []) > 0
        except:
            return False
    
    async def _get_context_item(self, organization_id: str, rag_feature: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific context item"""
        try:
            result = self.supabase.from_('rag_context_items').select('*').eq('organization_id', organization_id).eq('rag_feature', rag_feature).eq('item_id', item_id).execute()
            return result.data[0] if result.data else None
        except:
            return None
