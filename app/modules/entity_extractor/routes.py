import logging
from typing import List

from fastapi import FastAPI, HTTPException
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import AzureOpenAIEmbeddings
from pydantic import BaseModel

from app.modules.entity_extractor.constants import EntityExtractorConstants
from common.repositories.artifact_repository import ArtifactRepository
from common.repositories.vector_repository import VectorRepository
from connectors.key_vault_connector import AzureKeyVaultConnector
from connectors.mysql_connector import MySQLConnector
from connectors.pgvector_connector import PgVectorConnector
from global_constants import GlobalConstants
from utils.threading_tools import ThreadingTool

app = FastAPI()

constants = EntityExtractorConstants
global_constants = GlobalConstants


class DocumentRequest(BaseModel):
    artifact_id: str
    document_pages: List[str]


class EmbeddingService:
    def __init__(self, logger):
        self.logger = logger
        self.thread_id = ThreadingTool.get_thread_id()
        self.mysql_session = MySQLConnector().get_session()
        self.pgvector_session = PgVectorConnector().get_session()

        kv_client = AzureKeyVaultConnector()

        embedding_deployment = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.embedding_deployment
        )

        azure_openai_api_key = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.azure_openai_api_key
        )

        azure_openai_endpoint = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.azure_openai_endpoint
        )

        self.embeddings = AzureOpenAIEmbeddings(deployment=embedding_deployment,
                                                api_key=azure_openai_api_key,
                                                azure_endpoint=azure_openai_endpoint)

        self.text_splitter = SemanticChunker(embeddings=self.embeddings,
                                             breakpoint_threshold_type=constants.text_splitter_breakpoint_threshold_type,
                                             breakpoint_threshold_amount=constants.text_splitter_breakpoint_threshold_amount)

    def chunk_text(self, artifact_id, document_pages):
        self.logger.info(
            f"Chunking-Embedding : {self.thread_id} :: {artifact_id} : Running Semantic Chunker"
        )

        chunk_results = self.text_splitter.split_documents(document_pages)

        self.logger.info(
            f"Chunking-Embedding : {self.thread_id} :: {artifact_id} : Completed Semantic Chunking - chunk_count:{len(chunk_results)}"
        )

        return chunk_results

    def ingest_embeddings(self, artifact_id, document_pages):
        text_chunks = self.chunk_text(artifact_id, document_pages)

        text_strings = [chunk.page_content for chunk in text_chunks]
        embedding_results = self.embeddings.embed_documents(text_strings)

        artifact_repository = ArtifactRepository(self.mysql_session)
        artifact = artifact_repository.find_by_id(artifact_id)

        vector_repository = VectorRepository(self.logger, self.pgvector_session)
        vector_repository.create_vector_embeddings(artifact, text_chunks, embedding_results)


@app.post("/embed_documents/")
async def embed_documents(request: DocumentRequest):
    logger = logging.getLogger("embedding_service")
    service = EmbeddingService(logger)

    try:
        service.ingest_embeddings(request.artifact_id, request.document_pages)
        return {"message": "Documents processed and embeddings created successfully"}
    except Exception as e:
        logger.error(f"Error processing documents: {e}")
        raise HTTPException(status_code=500, detail="Error processing documents")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
