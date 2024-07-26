import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
from connectors.key_vault_connector import AzureKeyVaultConnector
from global_constants import GlobalConstants


class Logging:
    def __init__(self):
        kv_client = AzureKeyVaultConnector()

        # Fetch the Azure Application Insights connection string from Key Vault
        self.ai_conn_string = kv_client.get_secret(
            GlobalConstants.keys_of_key_vault_secrets.app_insights_conn_string
        )

        # Configure logger
        self.logger = logging.getLogger(__name__)

        # Set log level to INFO
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "[%(asctime)s.%(msecs)03d] [%(process)d] [%(levelname)s] %(message)s",
            datefmt="%Y:%m:%d %I:%M:%S",
        )
        # Add AzureLogHandler to the logger
        self.azure_handler = AzureLogHandler(connection_string=self.ai_conn_string)
        self.azure_handler.setFormatter(formatter)
        self.logger.addHandler(self.azure_handler)

        # Add Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def get_logger(self)-> logging.Logger:
        return self.logger
