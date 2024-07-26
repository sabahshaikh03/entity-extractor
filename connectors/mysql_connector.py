import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


class MySQLConnector:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT')
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        db_pass = os.getenv('DB_PASS')

        self.database_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

        # Print the database URL for debugging
        print(f"Database URL: {self.database_url}")

        self.engine = create_engine(self.database_url, echo=False)

    def get_session(self):
        Session = sessionmaker(bind=self.engine)
        return Session()

# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base, Session
# from connectors.key_vault_connector import AzureKeyVaultConnector
# from global_constants import GlobalConstants
# from common.mysql_declarative_base import Base
#
# global_constants = GlobalConstants
#
#
# class MySQLConnector:
#     def _init_(self):
#         kv_client = AzureKeyVaultConnector()
#         username = kv_client.get_secret(
#             global_constants.keys_of_key_vault_secrets.mysql_username
#         )
#         password = kv_client.get_secret(
#             global_constants.keys_of_key_vault_secrets.mysql_password
#         )
#         host = kv_client.get_secret(
#             global_constants.keys_of_key_vault_secrets.mysql_host
#         )
#         port = kv_client.get_secret(
#             global_constants.keys_of_key_vault_secrets.mysql_port
#         )
#         database = kv_client.get_secret(
#             global_constants.keys_of_key_vault_secrets.mysql_database
#         )
#
#         self.database_url = (
#             f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/{database}"
#         )
#         self.engine = create_engine(self.database_url, echo=False)
#         self.Session = sessionmaker(bind=self.engine)
#         self.Base = Base
#
#     def get_session(self) -> Session:
#         return self.Session()
#
#     def create_tables(self):
#         self.Base.metadata.create_all(self.engine)