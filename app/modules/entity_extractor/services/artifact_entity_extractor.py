import asyncio
from collections import namedtuple

from pypdf import PdfReader
from sqlalchemy.orm import Session

# noinspection PyUnresolvedReferences
from app.modules.artifact_ingestor.enums.blob_storage_types import BlobStorageTypes
from app.modules.entity_extractor.constants import EntityExtractorConstants
from app.modules.entity_extractor.services.embedding_service import EmbeddingService
from common.repositories.vector_repository import VectorRepository
from connectors.blob_storage_connector import AzureBlobStorageConnector
from connectors.key_vault_connector import AzureKeyVaultConnector
from global_constants import GlobalConstants
from utils.azure_blob_storage import BlobStorage
from utils.encoding import Encoding
# noinspection PyUnresolvedReferences
from utils.exceptions import CommonException
from utils.llm_invoker import LLMInvoker
from utils.threading_tools import ThreadingTool

global_constants = GlobalConstants
constants = EntityExtractorConstants

DocumentPage = namedtuple('DocumentPage', ['page_content', 'metadata'])

class ArtifactEntityExtractor:
    def __init__(self, logger, session):
        self.logger = logger
        self.thread_id = ThreadingTool.get_thread_id()
        self.asyncio_event_loop = asyncio.new_event_loop()
        self.session = session

        kv_client = AzureKeyVaultConnector()
        self.encoder = Encoding()
        self.embedding_service = EmbeddingService(logger)
        self.vector_repository = VectorRepository(logger, session=self.session)
        self.llm_invoker = LLMInvoker(logger, self.embedding_service.pgvector_session)

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

        self.viridium_blob_storage_util = BlobStorage(
            AzureBlobStorageConnector(
                viridium_blob_storage_conn_string, viridium_blob_storage_container_name
            ).connect(),
            self.logger,
        )

        self.customer_blob_storage_util = BlobStorage(
            AzureBlobStorageConnector(
                global_blob_storage_conn_string, global_blob_storage_container_name
            ).connect(),
            self.logger,
        )

        self.logger.info(
            f"Artifact-Entity-Extractor : {self.thread_id} ::  : Class Initialized"
        )

    def extract_entity(self, artifact_id):
        try:
            self.logger.info(
                f"Artifact-Entity-Extractor : {self.thread_id} :: {artifact_id} : Extract entity started"
            )

            # Using the new method for extracting text using PyPDFLoader
            document_pages = self.extract_text_with_pypdf('C:\\Users\\Shireen\\Desktop\\ingestion\\ingestion\\experiment\\test_docs\\Cadmium Nitrate_by Chem Service_SDS_S-M.pdf')

            self.embedding_service.ingest_embeddings(artifact_id, document_pages)

            content_embeddings = self.vector_repository.retrieve_embeddings(artifact_id, self.session)

            return self.get_material_response(artifact_id, content_embeddings)

        except Exception as exception:
            self.logger.exception(
                f"Artifact-Entity-Extractor : {self.thread_id} :: {artifact_id} : Exception :: {str(exception)}"
            )

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
            llm_invoker = LLMInvoker(self.logger, self.embedding_service.pgvector_session)

            material_response, material_cost, material_tokens = llm_invoker.get_material_info(material_docs, material_query, self.llm_invoker.material_extraction_prompt | self.llm_invoker.material_model | self.llm_invoker.json_parser)
            chemical_response, chemical_cost, chemical_tokens = llm_invoker.get_material_info(chemical_docs, chemical_query, self.llm_invoker.material_extraction_prompt | self.llm_invoker.material_composition_model | self.llm_invoker.json_parser)

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

        reader = PdfReader(local_pdf_path)
        document_pages = []
        for page in reader.pages:
            document_pages.append(DocumentPage(page_content=page.extract_text(), metadata={}))

        return document_pages

    def download_pdf_from_url(self, file_url):
        # Implement the logic to download the PDF from the blob URL to a local path
        # For example, using requests or another method to fetch the PDF file
        pass
