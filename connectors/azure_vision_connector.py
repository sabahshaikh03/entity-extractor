import os
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.core.credentials import AzureKeyCredential
from connectors.key_vault_connector import AzureKeyVaultConnector


class AzureVisionConnector:

    def __init__(self, global_constants):
        self.global_constants = global_constants

        kv_client = AzureKeyVaultConnector(self.global_constants)

        self.endpoint = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.azure_vision_ai_endpoint
        )
        self.key = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.azure_vision_ai_key
        )

    def connect(self):
        client = ImageAnalysisClient(
            endpoint=self.endpoint, credential=AzureKeyCredential(self.key)
        )
        return client
