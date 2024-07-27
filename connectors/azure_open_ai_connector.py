from openai import AzureOpenAI
from connectors.key_vault_connector import AzureKeyVaultConnector
from global_constants import GlobalConstants

global_constants = GlobalConstants


class AzureOpenAIConnector:
    def __init__(self):
        kv_client = AzureKeyVaultConnector()
        self.endpoint = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.azure_openai_endpoint
        )
        self.api_key = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.azure_openai_key
        )
        self.api_version = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.azure_openai_version
        )

    def connect(self):
        client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
        )
        return client
