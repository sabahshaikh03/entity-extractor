from azure.storage.blob import BlobServiceClient
from connectors.key_vault_connector import AzureKeyVaultConnector


class AzureBlobStorageConnector:

    def __init__(self, global_constants):
        self.global_constants = global_constants
        kv_client = AzureKeyVaultConnector(self.global_constants)

        self.connection_string = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.blob_storage_conn_string
        )
        self.container_name = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.blob_storage_container_name
        )

    def connect(self):
        blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )
        container_client = blob_service_client.get_container_client(self.container_name)

        return container_client
