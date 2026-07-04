import os
from supabase import create_client, Client

_url = os.environ["SUPABASE_URL"]
_key = os.environ["SUPABASE_SERVICE_KEY"]

supabase: Client = create_client(_url, _key)
