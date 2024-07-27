import os
from langchain_openai.embeddings import AzureOpenAIEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from app.modules.entity_extractor.constants import EntityExtractorConstants
from common.repositories.artifact_repository import ArtifactRepository
from common.repositories.vector_repository import VectorRepository
from connectors.key_vault_connector import AzureKeyVaultConnector
from connectors.mysql_connector import MySQLConnector
from connectors.pgvector_connector import PgVectorConnector
from utils.threading_tools import ThreadingTool

from utils.mysql import MySQL
from connectors.mysql_connector import MySQLConnector
from common.models.artifacts import Artifacts


# Service for chunking text and creating embeddings
class EmbeddingService:
    def __init__(self, logger):
        self.logger = logger
        self.thread_id = ThreadingTool.get_thread_id()
        self.mysql_session = None
        self.pgvector_session = None

        self.constants = EntityExtractorConstants()

        self.api_key = self.constants.azure_openai_api_key
        self.endpoint = self.constants.azure_openai_endpoint

        self.embeddings = AzureOpenAIEmbeddings(
            deployment=self.constants.embedding_deployment,
            api_key=self.constants.azure_openai_api_key,
            azure_endpoint=self.constants.azure_openai_endpoint
        )
        # Configure the text splitter
        self.text_splitter = SemanticChunker(
            embeddings=self.embeddings,
            breakpoint_threshold_type=EntityExtractorConstants.text_splitter_breakpoint_threshold_type,
            breakpoint_threshold_amount=EntityExtractorConstants.text_splitter_breakpoint_threshold_amount,
        )

    def set_sessions(self, mysql_session, pgvector_session=None):
        self.mysql_session = mysql_session
        if pgvector_session:
            self.pgvector_session = pgvector_session

    def close_sessions(self):
        try:
            if self.mysql_session:
                self.mysql_session.close()
            if self.pgvector_session:
                self.pgvector_session.close()
        except Exception as e:
            self.logger.error(f"Error closing sessions: {e}")

    def chunk_text(self, artifact_id, document_pages):
        self.logger.info(
            f"Chunking-Embedding : {self.thread_id} :: {artifact_id} : Running Semantic Chunker"
        )

        # Use split_documents correctly
        chunk_results = self.text_splitter.split_documents(document_pages)

        self.logger.info(
            f"Chunking-Embedding : {self.thread_id} :: {artifact_id} : Completed Semantic Chunking - chunk_count:{len(chunk_results)}"
        )

        return chunk_results

    def ingest_embeddings(self, artifact_id, document_pages):
        print("Passed to ingest_embeddings")
        try:
            print("Passing to text chunking ")
            text_chunks = self.chunk_text(artifact_id, document_pages)

            print("Trying to create embeddings ")
            text_strings = [chunk.page_content for chunk in text_chunks]
            embedding_results = self.embeddings.embed_documents(text_strings)
            print("Embeddings created")

            print("Establishing connection with MySQL")
            with MySQLConnector().get_session() as mysql_session:
                mysql_util = MySQL(
                    logger=self.logger,
                    session=mysql_session,
                    table=Artifacts,
                )

                artifact = mysql_util.get_entry_by_primary_key(artifact_id)
                print(f"ARTIFACT DETAILS: {artifact}")
                print(f"{artifact.id}")
                print(f"{artifact.name}")
                self.set_sessions(mysql_session)  # Set the session in the embedding service

            # Establish PgVector connection
            pgvector_connector = PgVectorConnector()
            with pgvector_connector.get_session() as pgvector_session:
                self.set_sessions(self.mysql_session, pgvector_session)

                print("passing to vector_repository")
                vector_repository = VectorRepository(self.logger, self.pgvector_session)
                vector_repository.create_vector_embeddings(artifact, text_chunks, embedding_results)
        finally:
            self.close_sessions()
