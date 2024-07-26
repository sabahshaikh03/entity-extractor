from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from connectors.key_vault_connector import AzureKeyVaultConnector
from global_constants import GlobalConstants

global_constants = GlobalConstants
Base = declarative_base()


class PgVectorConnector:
    def __init__(self):
        kv_client = AzureKeyVaultConnector()
        username = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.pgvector_username
        )
        password = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.pgvector_password
        )
        host = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.pgvector_host
        )
        port = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.pgvector_port
        )
        database = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.pgvector_database
        )

        # TODO: Do we need to include dialect in db_URL like this f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
        self.database_url = (
            f"postgresql://{username}:{password}@{host}:{port}/{database}"
        )
        self.engine = create_engine(self.database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self.Base = Base

    def get_session(self) -> Session:
        return self.Session()

    def create_tables(self):
        self.Base.metadata.create_all(self.engine)
