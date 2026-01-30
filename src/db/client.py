
from functools import lru_cache

from supabase import Client, create_client

from src.config import settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Get or create a singleton Supabase client.
    
    Returns:
        Configured Supabase client instance.
    """
    return create_client(settings.supabase_url, settings.supabase_key)
