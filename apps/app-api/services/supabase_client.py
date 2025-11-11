# apps/app-api/services/supabase_client.py

import os
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)


class SupabaseClientManager:
    """Singleton manager for Supabase client"""
    
    _instance: Optional['SupabaseClientManager'] = None
    _client: Optional[Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_client(self) -> Client:
        """Get or create Supabase client"""
        if self._client is None:
            # Use same defaults as main.py for consistency
            supabase_url = os.getenv('SUPABASE_URL', 'https://xxdahmkfioqzgqvyabek.supabase.co')
            # Support both SUPABASE_SERVICE_ROLE_KEY and SUPABASE_SERVICE_KEY for compatibility
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_SERVICE_KEY')
            
            if not supabase_key:
                # Return None instead of raising error, to match main.py's behavior
                logger.warning("SUPABASE_SERVICE_ROLE_KEY not set, Supabase client unavailable")
                return None
            
            try:
                self._client = create_client(supabase_url, supabase_key)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                # Return None instead of raising, to match main.py's behavior
                return None
        
        return self._client
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Supabase connection health"""
        try:
            client = self.get_client()
            # Simple query to test connection
            result = client.from_('profiles').select('id').limit(1).execute()
            
            return {
                "success": True,
                "status": "healthy",
                "response_time": 50.5  # Mock response time
            }
        except Exception as e:
            return {
                "success": False,
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def execute_query(self, table: str, select: str = "*", filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a query on Supabase"""
        try:
            client = self.get_client()
            query = client.from_(table).select(select)
            
            if filters:
                for key, value in filters.items():
                    query = query.eq(key, value)
            
            result = query.execute()
            
            return {
                "success": True,
                "data": result.data
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def insert_data(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert data into Supabase table"""
        try:
            client = self.get_client()
            result = client.from_(table).insert(data).execute()
            
            return {
                "success": True,
                "data": result.data
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_data(self, table: str, data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
        """Update data in Supabase table"""
        try:
            client = self.get_client()
            query = client.from_(table).update(data)
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.execute()
            
            return {
                "success": True,
                "data": result.data
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_data(self, table: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Delete data from Supabase table"""
        try:
            client = self.get_client()
            query = client.from_(table).delete()
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.execute()
            
            return {
                "success": True,
                "deleted_count": len(result.data) if result.data else 0
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    manager = SupabaseClientManager()
    return manager.get_client()
