import os
import requests
from typing import Dict

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "devops-lw3-root-token")

def get_vault_secret(path: str = "secret/data/db") -> Dict[str, str]:  # ← /data/db
    """Получает секрет из Vault KV v2."""
    url = f"{VAULT_ADDR}/v1/{path}"
    headers = {"X-Vault-Token": VAULT_TOKEN}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()["data"]["data"]

def get_db_url() -> str:
    """Формирует Database URL из секретов Vault."""
    secrets = get_vault_secret()
    return (
        f"postgresql+asyncpg://{secrets['DB_USER']}:{secrets['DB_PASS']}"
        f"@{secrets['DB_HOST']}:{secrets['DB_PORT']}/{secrets['DB_NAME']}"
    )