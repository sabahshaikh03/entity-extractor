import os
from langchain_openai import AzureOpenAIEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from app.modules.entity_extractor.constants import EntityExtractorConstants
from common.repositories.artifact_repository import ArtifactRepository
from common.repositories.vector_repository import VectorRepository
from connectors.key_vault_connector import AzureKeyVaultConnector
from connectors.mysql_connector import MySQLConnector
from connectors.pgvector_connector import PgVectorConnector
from utils.threading_tools import ThreadingTool


# Commenting out global_constants and key vault related code
# from global_constants import GlobalConstants
# global_constants = GlobalConstants

# Service for chunking text and creating embeddings
class EmbeddingService:
    def __init__(self, logger):
        self.logger = logger
        self.thread_id = ThreadingTool.get_thread_id()
        self.mysql_session = None
        self.pgvector_session = None

        self.initialize_sessions()

        embedding_deployment = os.getenv('EMBEDDING_DEPLOYMENT')
        azure_openai_api_key = os.getenv('AZURE_OPENAI_API_KEY')
        azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')

        self.embeddings = AzureOpenAIEmbeddings(deployment=embedding_deployment,
                                                api_key=azure_openai_api_key,
                                                azure_endpoint=azure_openai_endpoint)

        # Configure the text splitter
        self.text_splitter = SemanticChunker(
            embeddings=self.embeddings,
            breakpoint_threshold_type=EntityExtractorConstants.text_splitter_breakpoint_threshold_type,
            breakpoint_threshold_amount=EntityExtractorConstants.text_splitter_breakpoint_threshold_amount,
        )

    def initialize_sessions(self):
        try:
            self.mysql_session = MySQLConnector().get_session()
            self.pgvector_session = PgVectorConnector().get_session()
        except Exception as e:
            self.logger.error(f"Error initializing sessions: {e}")
            raise

    def close_sessions(self):
        try:
            if self.mysql_session:
                self.mysql_session.close()
            if self.pgvector_session:
                self.pgvector_session.close()
        except Exception as e:
            self.logger.error(f"Error closing sessions: {e}")

    def chunk_text(self, artifact_id, document_pages):
        # Process the text to chunk and create embeddings
        self.logger.info(
            f"Chunking-Embedding : {self.thread_id} :: {artifact_id} : Running Semantic Chunker"
        )

        chunk_results = self.text_splitter.split_documents(document_pages)
        print(chunk_results)

        self.logger.info(
            f"Chunking-Embedding : {self.thread_id} :: {artifact_id} : Completed Semantic Chunking - chunk_count:{len(chunk_results)}"
        )

        return chunk_results

    def ingest_embeddings(self, artifact_id, document_pages):
        try:
            text_chunks = self.chunk_text(artifact_id, document_pages)

            text_strings = [chunk.page_content for chunk in text_chunks]
            embedding_results = self.embeddings.embed_documents(text_strings)

            artifact_repository = ArtifactRepository(self.mysql_session)
            artifact = artifact_repository.find_by_id(artifact_id)

            vector_repository = VectorRepository(self.logger, self.pgvector_session)
            vector_repository.create_vector_embeddings(artifact, text_chunks, embedding_results)
        finally:
            self.close_sessions()
