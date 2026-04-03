import hvac
import os
import logging

logger = logging.getLogger(__name__)

class VaultManager:
    def __init__(self):
        self.vault_url = os.getenv("VAULT_ADDR", "http://vault:8200")
        self.token = os.getenv("VAULT_TOKEN")
        print(f"DEBUG: Vault Token is {'set' if self.token else 'NOT SET'}")
        self.client = hvac.Client(url=os.getenv("VAULT_ADDR"), token=self.token)

    def get_db_secrets(self):
        try:
            # mount_point='secret' - hvac использует путь /v1/secret/data/
            read_response = self.client.secrets.kv.v2.read_secret_version(
                path='oracle-db-creds',
                mount_point='secret'
            )
            # В KV v2 данные лежат в ['data']['data']
            return read_response['data']['data']
        except Exception as e:
            # полную ошибку для диагностики
            print(f"❌ Vault Error: {e}")
            return None

vault_manager = VaultManager()