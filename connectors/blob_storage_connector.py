from azure.storage.blob import BlobServiceClient
from connectors.key_vault_connector import AzureKeyVaultConnector
from global_constants import GlobalConstants

global_constants = GlobalConstants


class AzureBlobStorageConnector:

    def __init__(self, connection_string=None, container_name=None):

        kv_client = AzureKeyVaultConnector()

        self.connection_string = (
            connection_string
            if connection_string is not None
            else kv_client.get_secret(
                global_constants.keys_of_key_vault_secrets.blob_storage_conn_string
            )
        )
        self.container_name = (
            container_name
            if container_name is not None
            else kv_client.get_secret(
                global_constants.keys_of_key_vault_secrets.blob_storage_container_name
            )
        )

    def connect(self)-> BlobServiceClient:
        blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )
        container_client = blob_service_client.get_container_client(self.container_name)

        return container_client
