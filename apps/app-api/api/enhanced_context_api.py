# apps/app-api/api/enhanced_context_api.py

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
from services.enhanced_context_manager import EnhancedContextManager
from services.audit_logger import audit_logger

router = APIRouter(prefix="/api/enhanced-context", tags=["Enhanced Context Management"])

# Initialize the enhanced context manager
context_manager = EnhancedContextManager()

# ==================== APP-WIDE CONTEXT ENDPOINTS ====================

@router.post("/global/add")
async def add_global_context_item(
    context_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add a new global context item accessible to all tenants"""
    try:
        # Only system admins can add global context
        if current_user.get('role') != 'system_admin':
            raise HTTPException(status_code=403, detail="Only system admins can add global context")
        
        result = await context_manager.add_global_context_item(context_data)
        
        # Log the action
        await audit_logger.log_user_action({
            "user_id": current_user['id'],
            "organization_id": "system",
            "action": "add_global_context",
            "resource_type": "global_context_item",
            "resource_id": result.get('item_id', 'unknown'),
            "details": {
                "rag_feature": context_data.get('rag_feature'),
                "item_title": context_data.get('item_title'),
                "success": result['success']
            }
        })
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/global/items")
async def get_global_context_items(
    rag_feature: Optional[str] = None,
    organization_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get global context items accessible to a tenant"""
    try:
        # Use user's organization if not specified
        if not organization_id:
            organization_id = current_user.get('organization_id')
        
        result = await context_manager.get_global_context_items(
            rag_feature=rag_feature,
            organization_id=organization_id,
            limit=limit,
            offset=offset
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== TENANT ACCESS MANAGEMENT ENDPOINTS ====================

@router.post("/access/grant")
async def grant_tenant_access(
    organization_id: str,
    rag_feature: str,
    access_level: str = "read",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Grant a tenant access to a global RAG feature"""
    try:
        # Only org admins and system admins can grant access
        if current_user.get('role') not in ['org_admin', 'system_admin']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Org admins can only grant access to their own organization
        if current_user.get('role') == 'org_admin' and current_user.get('organization_id') != organization_id:
            raise HTTPException(status_code=403, detail="Can only grant access to your own organization")
        
        result = await context_manager.grant_tenant_access(
            organization_id=organization_id,
            rag_feature=rag_feature,
            access_level=access_level
        )
        
        # Log the action
        await audit_logger.log_user_action({
            "user_id": current_user['id'],
            "organization_id": organization_id,
            "action": "grant_tenant_access",
            "resource_type": "tenant_access",
            "resource_id": result.get('access_id', 'unknown'),
            "details": {
                "rag_feature": rag_feature,
                "access_level": access_level,
                "success": result['success']
            }
        })
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/access/revoke")
async def revoke_tenant_access(
    organization_id: str,
    rag_feature: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Revoke a tenant's access to a global RAG feature"""
    try:
        # Only org admins and system admins can revoke access
        if current_user.get('role') not in ['org_admin', 'system_admin']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Org admins can only revoke access from their own organization
        if current_user.get('role') == 'org_admin' and current_user.get('organization_id') != organization_id:
            raise HTTPException(status_code=403, detail="Can only revoke access from your own organization")
        
        result = await context_manager.revoke_tenant_access(
            organization_id=organization_id,
            rag_feature=rag_feature
        )
        
        # Log the action
        await audit_logger.log_user_action({
            "user_id": current_user['id'],
            "organization_id": organization_id,
            "action": "revoke_tenant_access",
            "resource_type": "tenant_access",
            "resource_id": result.get('revoked_id', 'unknown'),
            "details": {
                "rag_feature": rag_feature,
                "success": result['success']
            }
        })
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CROSS-TENANT SHARING ENDPOINTS ====================

@router.post("/sharing/share")
async def share_context_item(
    target_organization_id: str,
    rag_feature: str,
    item_id: str,
    sharing_type: str = "read_only",
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Share a context item with another tenant"""
    try:
        # Only org admins and system admins can share
        if current_user.get('role') not in ['org_admin', 'system_admin']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        source_organization_id = current_user.get('organization_id')
        
        result = await context_manager.share_context_item(
            source_org_id=source_organization_id,
            target_org_id=target_organization_id,
            rag_feature=rag_feature,
            item_id=item_id,
            sharing_type=sharing_type,
            shared_by=current_user['id']
        )
        
        # Log the action
        await audit_logger.log_user_action({
            "user_id": current_user['id'],
            "organization_id": source_organization_id,
            "action": "share_context_item",
            "resource_type": "context_sharing",
            "resource_id": result.get('sharing_id', 'unknown'),
            "details": {
                "target_organization_id": target_organization_id,
                "rag_feature": rag_feature,
                "item_id": item_id,
                "sharing_type": sharing_type,
                "success": result['success']
            }
        })
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sharing/approve/{sharing_id}")
async def approve_sharing_request(
    sharing_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Approve a context sharing request"""
    try:
        # Only org admins and system admins can approve
        if current_user.get('role') not in ['org_admin', 'system_admin']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        result = await context_manager.approve_sharing_request(
            sharing_id=sharing_id,
            approved_by=current_user['id']
        )
        
        # Log the action
        await audit_logger.log_user_action({
            "user_id": current_user['id'],
            "organization_id": current_user.get('organization_id'),
            "action": "approve_sharing_request",
            "resource_type": "context_sharing",
            "resource_id": sharing_id,
            "details": {
                "success": result['success']
            }
        })
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sharing/received")
async def get_shared_context_items(
    rag_feature: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get context items shared with the current user's organization"""
    try:
        organization_id = current_user.get('organization_id')
        
        result = await context_manager.get_shared_context_items(
            organization_id=organization_id,
            rag_feature=rag_feature
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== ENHANCED UPLOAD ENDPOINTS ====================

@router.post("/upload/file")
async def upload_file_content(
    file: UploadFile = File(...),
    rag_feature: str = Form(...),
    organization_id: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Upload and process file content"""
    try:
        # Use user's organization if not specified
        if not organization_id:
            organization_id = current_user.get('organization_id')
        
        # Read file content
        content = await file.read()
        file_content = content.decode('utf-8')
        
        # Parse metadata if provided
        parsed_metadata = json.loads(metadata) if metadata else {}
        
        result = await context_manager.upload_file_content(
            file_content=file_content,
            file_type=file.filename.split('.')[-1] if '.' in file.filename else 'txt',
            organization_id=organization_id,
            rag_feature=rag_feature,
            uploaded_by=current_user['id'],
            metadata=parsed_metadata
        )
        
        # Log the action
        await audit_logger.log_user_action({
            "user_id": current_user['id'],
            "organization_id": organization_id,
            "action": "upload_file_content",
            "resource_type": "file_upload",
            "resource_id": f"file_{file.filename}",
            "details": {
                "filename": file.filename,
                "rag_feature": rag_feature,
                "success_count": result.get('success_count', 0),
                "error_count": result.get('error_count', 0),
                "success": result['success']
            }
        })
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/web-scrape")
async def scrape_web_content(
    url: str,
    rag_feature: str,
    organization_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Scrape web content and add to context"""
    try:
        # Use user's organization if not specified
        if not organization_id:
            organization_id = current_user.get('organization_id')
        
        result = await context_manager.scrape_web_content(
            url=url,
            organization_id=organization_id,
            rag_feature=rag_feature,
            uploaded_by=current_user['id']
        )
        
        # Log the action
        await audit_logger.log_user_action({
            "user_id": current_user['id'],
            "organization_id": organization_id,
            "action": "scrape_web_content",
            "resource_type": "web_scrape",
            "resource_id": url,
            "details": {
                "url": url,
                "rag_feature": rag_feature,
                "success": result['success']
            }
        })
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload/bulk")
async def bulk_api_upload(
    items: List[Dict[str, Any]],
    rag_feature: str,
    organization_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Bulk upload via API"""
    try:
        # Use user's organization if not specified
        if not organization_id:
            organization_id = current_user.get('organization_id')
        
        result = await context_manager.bulk_api_upload(
            items=items,
            organization_id=organization_id,
            rag_feature=rag_feature,
            uploaded_by=current_user['id']
        )
        
        # Log the action
        await audit_logger.log_user_action({
            "user_id": current_user['id'],
            "organization_id": organization_id,
            "action": "bulk_api_upload",
            "resource_type": "bulk_upload",
            "resource_id": f"bulk_{len(items)}_items",
            "details": {
                "items_count": len(items),
                "rag_feature": rag_feature,
                "success_count": result.get('success_count', 0),
                "error_count": result.get('error_count', 0),
                "success": result['success']
            }
        })
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== QUOTA MANAGEMENT ENDPOINTS ====================

@router.get("/quotas/{organization_id}")
async def get_organization_quotas(
    organization_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get organization's context quotas and usage"""
    try:
        # Only org admins and system admins can view quotas
        if current_user.get('role') not in ['org_admin', 'system_admin']:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Org admins can only view their own organization's quotas
        if current_user.get('role') == 'org_admin' and current_user.get('organization_id') != organization_id:
            raise HTTPException(status_code=403, detail="Can only view your own organization's quotas")
        
        result = await context_manager.get_organization_quotas(organization_id)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/quotas/{organization_id}")
async def update_organization_quotas(
    organization_id: str,
    quota_updates: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update organization's context quotas"""
    try:
        # Only system admins can update quotas
        if current_user.get('role') != 'system_admin':
            raise HTTPException(status_code=403, detail="Only system admins can update quotas")
        
        result = await context_manager.update_organization_quotas(
            organization_id=organization_id,
            quota_updates=quota_updates
        )
        
        # Log the action
        await audit_logger.log_user_action({
            "user_id": current_user['id'],
            "organization_id": organization_id,
            "action": "update_organization_quotas",
            "resource_type": "organization_quotas",
            "resource_id": organization_id,
            "details": {
                "quota_updates": quota_updates,
                "success": result['success']
            }
        })
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== HELPER FUNCTIONS ====================

async def get_current_user() -> Dict[str, Any]:
    """Get current user from authentication (placeholder implementation)"""
    # This would integrate with your authentication system
    # For now, return a mock user
    return {
        "id": "user-123",
        "role": "system_admin",
        "organization_id": "org-123"
    }
