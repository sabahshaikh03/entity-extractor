import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
from connectors.key_vault_connector import AzureKeyVaultConnector


class Logging:
    def __init__(self, global_constants):
        self.global_constants = global_constants

        kv_client = AzureKeyVaultConnector(self.global_constants)

        # Fetch the Azure Application Insights connection string from Key Vault
        self.ai_conn_string = kv_client.get_secret(
            self.global_constants.keys_of_key_vault_secrets.app_insights_conn_string
        )

        # Configure logger
        self.logger = logging.getLogger(__name__)

        # Set log level to INFO
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter("[%(process)d] [%(levelname)s] %(message)s")
        # Add AzureLogHandler to the logger
        self.azure_handler = AzureLogHandler(connection_string=self.ai_conn_string)
        self.azure_handler.setFormatter(formatter)
        self.logger.addHandler(self.azure_handler)

        # Add Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger
