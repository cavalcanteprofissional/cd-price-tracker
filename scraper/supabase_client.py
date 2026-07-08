import os
from supabase import create_client, Client

_url = os.environ.get("SUPABASE_URL", "")
_key = os.environ.get("SUPABASE_SERVICE_KEY", "")

supabase: Client = create_client(_url, _key)
