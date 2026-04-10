from app.core.config import get_settings
from supabase import create_client
import asyncio
import json

async def main():
    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_service_key)
    result = client.table("templates").select("structure_json").limit(1).execute()
    print(json.dumps(result.data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
