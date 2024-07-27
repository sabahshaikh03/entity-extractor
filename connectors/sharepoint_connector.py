import os
from msgraph import GraphServiceClient
from azure.identity.aio import ClientSecretCredential
from connectors.key_vault_connector import AzureKeyVaultConnector
from global_constants import GlobalConstants

global_constants = GlobalConstants


class SharePointConnector:
    
    def __init__(self):
            
        kv_client = AzureKeyVaultConnector()

        self.client_id = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.sharepoint_client_id
        )
        self.tenant_id = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.sharepoint_tenant_id
        )
        self.client_secret = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.sharepoint_client_secret
        )

    def get_client(self) -> GraphServiceClient:
        try:
            creds = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret,
            )
            client = GraphServiceClient(
                credentials=creds, scopes=[global_constants.graph_service_scope]
            )
            return client
        except Exception as e:
            return None