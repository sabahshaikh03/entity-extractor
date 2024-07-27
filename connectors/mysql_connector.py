from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from connectors.key_vault_connector import AzureKeyVaultConnector
from global_constants import GlobalConstants
from common.mysql_declarative_base import Base

global_constants = GlobalConstants


class MySQLConnector:
    def __init__(self):
        kv_client = AzureKeyVaultConnector()
        username = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.mysql_username
        )
        password = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.mysql_password
        )
        host = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.mysql_host
        )
        port = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.mysql_port
        )
        database = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.mysql_database
        )

        self.database_url = (
            f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
        )
        self.engine = create_engine(self.database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self.Base = Base

    def get_session(self) -> Session:
        return self.Session()

    def create_tables(self):
        self.Base.metadata.create_all(self.engine)
