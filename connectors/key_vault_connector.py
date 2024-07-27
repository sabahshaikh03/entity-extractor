import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ResourceNotFoundError


class AzureKeyVaultConnector:
    def __init__(self, global_constants):
        self.global_constants = global_constants
        self.kv_uri = self.global_constants.azure_kv_uri
        if self.check_if_required_azure_vars_available() and self.kv_uri is not None:
            try:
                credential = DefaultAzureCredential()
                self.kv_client = SecretClient(
                    vault_url=self.kv_uri, credential=credential
                )
            except Exception as e:
                self.kv_client = None
        else:
            self.kv_client = None

    def check_if_required_azure_vars_available(self):
        return (
            os.getenv(self.global_constants.azure_client_id) is not None
            and os.getenv(self.global_constants.azure_client_secret) is not None
            and os.getenv(self.global_constants.azure_tenant_id) is not None
        )

    def get_secret(self, key):
        if self.kv_client is not None:
            try:
                return self.kv_client.get_secret(key).value
            except ResourceNotFoundError:
                return os.getenv(key, None)
        else:
            return os.getenv(key, None)

    def connect(self):
        return self.kv_client
