import os
from functools import lru_cache

from dotenv import load_dotenv
from supabase import Client, create_client

from config.settings import BASE_PATH


# Conexão com o banco de dados
@lru_cache(maxsize=1)
def get_supabase() -> Client:
    env_path = BASE_PATH / ".env"
    load_dotenv(dotenv_path=env_path, override=False)

    url = os.getenv("SUPABASE_URL", "").strip()
    key = (
        os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
        or os.getenv("SUPABASE_KEY", "").strip()
    )

    if not url or not key:
        raise RuntimeError(
            "Supabase não configurado"
        )

    return create_client(url, key)
