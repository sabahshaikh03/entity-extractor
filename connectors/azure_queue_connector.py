from azure.storage.queue import QueueClient
from connectors.key_vault_connector import AzureKeyVaultConnector


class AzureQueueConnector:
    def __init__(self, global_constants):
        self.global_constants = global_constants
        # Instantiate AzureKeyVaultConnector
        kv_client = AzureKeyVaultConnector(self.global_constants)

        # Get connection string and queue name from Key Vault
        self.connection_string = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.azure_queue_conn_string
        )
        self.queue_name = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.queue_name
        )

    def connect(self):
        # Create and return QueueClient
        return QueueClient.from_connection_string(
            self.connection_string, queue_name=self.queue_name
        )
