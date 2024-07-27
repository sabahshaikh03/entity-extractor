import asyncio
from collections import namedtuple

from langchain_community.document_loaders import PyPDFLoader
from connectors.pgvector_connector import PgVectorConnector
from app.modules.artifact_ingestor.enums.blob_storage_types import BlobStorageTypes
from app.modules.entity_extractor.constants import EntityExtractorConstants
from app.modules.entity_extractor.services.embedding_service import EmbeddingService
from common.repositories.vector_repository import VectorRepository
from connectors.blob_storage_connector import AzureBlobStorageConnector
from connectors.key_vault_connector import AzureKeyVaultConnector
from global_constants import GlobalConstants
from utils.azure_blob_storage import BlobStorage
from utils.encoding import Encoding
from utils.exceptions import CommonException
from utils.llm_invoker import LLMInvoker
from utils.threading_tools import ThreadingTool
from utils.mysql import MySQL
from connectors.mysql_connector import MySQLConnector
from common.models.artifacts import Artifacts

global_constants = GlobalConstants
constants = EntityExtractorConstants

class ArtifactEntityExtractor:
    def __init__(self, logger):
        self.logger = logger
        self.thread_id = ThreadingTool.get_thread_id()
        self.asyncio_event_loop = asyncio.new_event_loop()

        self.pgvector_connector = PgVectorConnector()
        self.pgvector_session = self.pgvector_connector.get_session()

        kv_client = AzureKeyVaultConnector()
        self.encoder = Encoding()
        self.embedding_service = EmbeddingService(logger)
        self.vector_repository = VectorRepository(logger, self.pgvector_session)
        self.llm_invoker = LLMInvoker(logger, self.pgvector_session)

        viridium_blob_storage_conn_string = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.blob_storage_conn_string
        )

        viridium_blob_storage_container_name = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.blob_storage_container_name
        )
        global_blob_storage_conn_string = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.blob_storage_conn_string
        )
        global_blob_storage_container_name = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.blob_storage_container_name
        )

        self.logger.info(
            f"Artifact-Entity-Extractor : {self.thread_id} ::  : Class Initialized"
        )

    def extract_entity(self, artifact_id):
        try:
            self.logger.info(f"Artifact-Entity-Extractor : {self.thread_id} :: {artifact_id} : Extract entity started")

            # Using the new method for extracting text using PyPDFLoader
            document_pages = self.extract_text_with_pypdf('C:\\Users\Shireen\Documents\ingestion\ingestion\experiment\test_docs\18.1 SDS 600 Grit Wet Dry Sandpaper.pdf')
            self.embedding_service.ingest_embeddings(artifact_id, document_pages)

            # Run the LLMInvoker's run method
            self.llm_invoker.set_session(self.pgvector_session)
            response = self.llm_invoker.run(artifact_id)
            self.logger.info("LLMInvoker run completed")

            print("\n\n\n\n\n\n\nRESPONSE",response)

            return response

        except Exception as exception:
            self.logger.exception(f"Artifact-Entity-Extractor : {self.thread_id} :: {artifact_id} : Exception :: {str(exception)}")

    def run_query_chain(self, relevant_docs):
        try:
            print("Running the chain")
            query = "Retrieve material information based on these embeddings."
            response, cost, tokens = self.llm_invoker.get_material_info(relevant_docs, query,
                                                                        self.llm_invoker.material_extraction_prompt)
            return response
        except Exception as exception:
            self.logger.exception(
                f"Artifact-Entity-Extractor : {self.thread_id} :: Exception in run_query_chain :: {str(exception)}")
            return None

    def get_material_response(self, artifact_id, embeddings):
        self.logger.info(
            f"Artifact-Entity-Extractor : {self.thread_id} :: {artifact_id} : Getting material response from OpenAI"
        )

        try:
            # Get query embeddings for material and composition
            material_query = "Retrieve material information based on these embeddings."
            chemical_query = "Retrieve chemical composition based on these embeddings."

            material_embeddings = self.embedding_service.embeddings.embed_documents([material_query])
            chemical_embeddings = self.embedding_service.embeddings.embed_documents([chemical_query])

            # Retrieve embeddings
            material_docs = self.vector_repository.retrieve_embeddings(artifact_id, material_embeddings[0])
            chemical_docs = self.vector_repository.retrieve_embeddings(artifact_id, chemical_embeddings[0])

            # Call LLM invoker
            self.llm_invoker.set_session(self.embedding_service.pgvector_session)  # Set the session in LLM invoker
            material_response, material_cost, material_tokens = self.llm_invoker.get_material_info(
                material_docs, material_query,
                self.llm_invoker.material_extraction_prompt | self.llm_invoker.material_model | self.llm_invoker.json_parser
            )
            chemical_response, chemical_cost, chemical_tokens = self.llm_invoker.get_material_info(
                chemical_docs, chemical_query,
                self.llm_invoker.material_extraction_prompt | self.llm_invoker.material_composition_model | self.llm_invoker.json_parser
            )

            # Merge responses
            merged_response = {
                "material_response": material_response,
                "chemical_response": chemical_response,
            }

            self.logger.info(
                f"Artifact-Entity-Extractor : {self.thread_id} :: {artifact_id} : Material response retrieved successfully"
            )

            return merged_response

        except Exception as exception:
            self.logger.exception(
                f"Artifact-Entity-Extractor : {self.thread_id} :: {artifact_id} : Exception while getting material response :: {str(exception)}"
            )
            return None

    def extract_text_with_pypdf(self, local_pdf_path):
        self.logger.info(
            f"Artifact-Entity-Extractor : {self.thread_id} :: Extracting text using PyPDFLoader from {local_pdf_path}"
        )

        documents = []
        loader = PyPDFLoader(local_pdf_path)
        document = loader.load()

        documents.extend(document)

        return documents

    def download_pdf_from_url(self, file_url):
        # Implement the logic to download the PDF from the blob URL to a local path
        # For example, using requests or another method to fetch the PDF file
        pass
