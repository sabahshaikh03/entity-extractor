import os
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.core.credentials import AzureKeyCredential
from connectors.key_vault_connector import AzureKeyVaultConnector
from global_constants import GlobalConstants

global_constants = GlobalConstants

class AzureVisionConnector:

    def __init__(self):
        
        kv_client = AzureKeyVaultConnector()

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