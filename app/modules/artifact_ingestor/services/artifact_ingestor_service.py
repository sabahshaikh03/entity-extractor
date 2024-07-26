import json
import fitz
import uuid
from logging import Logger
from typing import List, Any
from collections import Counter
from global_constants import GlobalConstants
from app.modules.artifact_ingestor.constants import Constants
from app.modules.artifact_ingestor.dto.artifact_input_dto import ArtifactInputDTO
from app.modules.artifact_ingestor.dto.chemical_dto import Chemical
from app.modules.artifact_ingestor.dto.msds_openai_response import MSDSAnalysis
from utils.exceptions import CommonException, LanguageModelException
from connectors.blob_storage_connector import AzureBlobStorageConnector
from utils.azure_blob_storage import BlobStorage
from connectors.sharepoint_connector import SharePointConnector
from utils.sharepoint import SharePoint
from connectors.key_vault_connector import AzureKeyVaultConnector
from utils.azure_open_ai import OpenAI
from app.modules.keyword_analysis.services.file_analysis_service import (
    FileAnalysisService,
)
from connectors.mysql_connector import MySQLConnector
from utils.mysql import MySQL
from utils.azure_queue import AzureQueue
from utils.encoding import Encoding

from app.modules.artifact_ingestor.enums.blob_storage_types import BlobStorageTypes
from app.modules.artifact_ingestor.enums.global_node_types import GlobalNodeTypes
from app.modules.artifact_ingestor.enums.pfas_information_sources import (
    PfasInformationSource,
)
from app.modules.artifact_ingestor.enums.pfas_statuses import PfasStatus
from app.modules.artifact_ingestor.enums.openai_pfas_statuses import OpenAiPfasStatus

from app.modules.artifact_ingestor.dto.response_entity_dto import ResponseEntityDTO
from app.modules.artifact_ingestor.dto.pfas_resolution import PFASResolution
from app.modules.artifact_ingestor.dto.chemical_openai_response import (
    ChemicalsOpenAiResponse,
)
from app.modules.artifact_ingestor.dto.artifact_ingestor_input_dto import (
    ArtifactIngestorInputDTO,
)

from app.modules.artifact_ingestor.models.artifact_upload_run_state_details import (
    ArtifactUploadRunStateDetails,
)
from common.models.artifacts import Artifacts
from app.modules.artifact_ingestor.models.manufacturer import Manufacturer
from app.modules.artifact_ingestor.models.global_node import GlobalNode
from app.modules.artifact_ingestor.models.document_metadata import DocumentMetadata
from app.modules.artifact_ingestor.models.material_to_document_mapping import (
    MaterialToDocumentMapping,
)
from app.modules.artifact_ingestor.models.material_to_document_mapping import (
    MaterialToDocumentCompositeKey,
)

from app.modules.artifact_ingestor.models.global_node_hierarchy import (
    GlobalNodeHierarchy,
    GlobalNodeHierarchyCompositeKey,
)

from common.repositories.artifact_repository import (
    ArtifactRepository,
)
from app.modules.artifact_ingestor.repositories.global_node_repository import (
    GlobalNodeRepo,
)
from app.modules.artifact_ingestor.repositories.manufacturer_repository import (
    ManufacturerRepo,
)
from app.modules.artifact_ingestor.repositories.document_metadata_repository import (
    DocumentMetadataRepo,
)
from app.modules.artifact_ingestor.repositories.global_node_hierarchy_repository import (
    GlobalNodeHierarchyRepo,
)
from app.modules.artifact_ingestor.repositories.material_to_document_mapping_repository import (
    MaterialToDocumentMappingRepo,
)

from app.modules.artifact_ingestor.enums.artifact_upload_statuses import (
    ArtifactUploadStatus,
)
from app.modules.artifact_ingestor.enums.artifact_run_state_detail_stage_names import (
    ArtifactRunStateDetailStageName,
)
from app.modules.artifact_ingestor.enums.artifact_run_state_detail_stage_statuses import (
    ArtifactRunStateDetailStageStatus,
)
from utils.threading_tools import ThreadingTool
from utils.task_visiblity_controller import TaskVisibilityController

global_constants = GlobalConstants
constants = Constants


class ArtifactIngestorService:
    def __init__(
        self,
        logger: Logger,
        asyncio_event_loop,
    ):
        self.logger = logger
        self.asyncio_event_loop = asyncio_event_loop
        self.azure_queue_util = AzureQueue()
        kv_client = AzureKeyVaultConnector()
        self.encoder = Encoding()

        system_blob_storage_conn_string = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.blob_storage_conn_string
        )
        system_blob_storage_container_name = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.blob_storage_container_name
        )
        global_blob_storage_conn_string = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.blob_storage_conn_string
        )
        global_blob_storage_container_name = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.blob_storage_container_name
        )

        self.internal_blob_storage_util = BlobStorage(
            AzureBlobStorageConnector(
                system_blob_storage_conn_string, system_blob_storage_container_name
            ).connect(),
            self.logger,
        )

        self.customer_blob_storage_util = BlobStorage(
            AzureBlobStorageConnector(
                global_blob_storage_conn_string, global_blob_storage_container_name
            ).connect(),
            self.logger,
        )

        self.ka_blob_storage_util = BlobStorage(
            AzureBlobStorageConnector(
                global_blob_storage_conn_string, global_blob_storage_container_name
            ).connect(),
            self.logger,
        )

        self.share_point_connector = SharePointConnector()
        self.sharepoint_client = self.share_point_connector.get_client()
        self.sharepoint_util = SharePoint(self.sharepoint_client)

        self.openai_util = OpenAI(
            logger=self.logger,
        )

        self.file_analysis_service = FileAnalysisService(logger)

        self.session = MySQLConnector().get_session()

        # Instantiate the artifact repository
        self.artifact_repo = ArtifactRepository(self.session)
        self.global_node_repo = GlobalNodeRepo(self.session)
        self.manufacturer_repo = ManufacturerRepo(self.session)
        self.document_metadata_repo = DocumentMetadataRepo(self.session)
        self.node_hierarchy_repo = GlobalNodeHierarchyRepo(self.session)
        self.material_to_document_mapping_repo = MaterialToDocumentMappingRepo(
            self.session
        )

    def update_artifact_run_state_stage(
        self,
        artifact_upload_run_state_id: str,
        stage_name: ArtifactRunStateDetailStageName,
        stage_status: ArtifactRunStateDetailStageStatus,
        mysql_run_state_detail_util: MySQL,
    ):
        folder_upload_table_record_data = {
            "id": artifact_upload_run_state_id,
            "completed_stage_name": stage_name.value,
            "completed_stage_status": stage_status.value,
        }
        mysql_run_state_detail_util.update_entry(
            artifact_upload_run_state_id, folder_upload_table_record_data
        )

    def ingest_artifact(
        self,
        artifact_ingestor_input_data: ArtifactIngestorInputDTO,
    ):
        try:
            thread_id = ThreadingTool.get_thread_id()
            artifact_run_state_id = (
                artifact_ingestor_input_data.artifact_upload_run_state_id
            )

            # Logging
            self.logger.info(
                f"Artifact-Upload : {thread_id} :: {artifact_run_state_id} : Ingestion started"
            )

            mysql_session = MySQLConnector().get_session()
            mysql_run_state_detail_util = MySQL(
                logger=self.logger,
                session=mysql_session,
                table=ArtifactUploadRunStateDetails,
            )

            artifact_input_data = ArtifactInputDTO(
                file_url=artifact_ingestor_input_data.artifact_file_url,
                source_name="exampleSource",
                source_link="http://example.com",
                data_format="JSON",
                upload_type="manual",
                domain="exampleDomain",
                sub_domain="exampleSubDomain",
                category="exampleCategory",
                type="MSDS",
                region="exampleRegion",
                country="exampleCountry",
                state="exampleState",
                city="exampleCity",
                organization="exampleOrg",
                trust_factor="high",
                status="active",
                enabled=True,
                name="exampleArtifactName",
                file_upload_type="SHAREPOINT",
            )

            self.update_artifact_run_state_stage(
                artifact_run_state_id,
                ArtifactRunStateDetailStageName.ADD_ARTIFACT,
                ArtifactRunStateDetailStageStatus.PROCESSING,
                mysql_run_state_detail_util,
            )

            # Add artifact entry to artifacts table and upload artifact to customer blob storage
            artifact = self.add_artifact(
                artifact_input_data=artifact_input_data,
            )

            self.logger.info(
                f"Artifact-Upload : {thread_id} :: {artifact_run_state_id} : Inserted data into artifact table"
            )

            self.update_artifact_run_state_stage(
                artifact_run_state_id,
                ArtifactRunStateDetailStageName.ADD_ARTIFACT,
                ArtifactRunStateDetailStageStatus.COMPLETED,
                mysql_run_state_detail_util,
            )

            # If the execution time reaches visibility time then extend the visibility time
            TaskVisibilityController.check_and_extend_visibility_timeout()

            if artifact_input_data.type == "MSDS":
                self.update_artifact_run_state_stage(
                    artifact_run_state_id,
                    ArtifactRunStateDetailStageName.ANALYZING,
                    ArtifactRunStateDetailStageStatus.PROCESSING,
                    mysql_run_state_detail_util,
                )

                # Analyze MSDS data
                msds_analysis = self.analyze_msds(
                    file=artifact_ingestor_input_data.artifact_file_url,
                    artifact=artifact,
                )

                self.logger.info(
                    f"Artifact-Upload : {thread_id} :: {artifact_run_state_id} : MSDS Anlyzed"
                )

                self.update_artifact_run_state_stage(
                    artifact_run_state_id,
                    ArtifactRunStateDetailStageName.ANALYZING,
                    ArtifactRunStateDetailStageStatus.COMPLETED,
                    mysql_run_state_detail_util,
                )

                # If the execution time reaches visibility time then extend the visibility time
                TaskVisibilityController.check_and_extend_visibility_timeout()

                self.update_artifact_run_state_stage(
                    artifact_run_state_id,
                    ArtifactRunStateDetailStageName.SAVING,
                    ArtifactRunStateDetailStageStatus.PROCESSING,
                    mysql_run_state_detail_util,
                )

                # Save MSDS analysis
                self.save_msds(msds_analysis=msds_analysis, artifact=artifact)
                self.logger.info(
                    f"Artifact-Upload : {thread_id} :: {artifact_run_state_id} : MSDS Data saved into mysql"
                )

                self.update_artifact_run_state_stage(
                    artifact_run_state_id,
                    ArtifactRunStateDetailStageName.SAVING,
                    ArtifactRunStateDetailStageStatus.COMPLETED,
                    mysql_run_state_detail_util,
                )

                if artifact.upload_status == ArtifactUploadStatus.STARTED:
                    self.update_artifact_run_state_stage(
                        artifact_run_state_id,
                        ArtifactRunStateDetailStageName.UPLOADING,
                        ArtifactRunStateDetailStageStatus.PROCESSING,
                        mysql_run_state_detail_util,
                    )

                    # Upload artifact to pg vector
                    self.upload_artifacts(
                        artifact.name,
                        artifact,
                    )

                    self.logger.info(
                        f"Artifact-Upload : {thread_id} :: {artifact_run_state_id} : MSDS uploaded to pg vector"
                    )

                    self.update_artifact_run_state_stage(
                        artifact_run_state_id,
                        ArtifactRunStateDetailStageName.UPLOADING,
                        ArtifactRunStateDetailStageStatus.COMPLETED,
                        mysql_run_state_detail_util,
                    )

            # If the execution time reaches visibility time then extend the visibility time
            TaskVisibilityController.check_and_extend_visibility_timeout()

        except CommonException as e:
            self.logger.exception(
                f"Artifact-Upload : {thread_id} :: {artifact_run_state_id} : Exception :{str(e.message)}"
            )
            if mysql_session and mysql_run_state_detail_util:
                folder_upload_table_record_data = {
                    "id": artifact_run_state_id,
                    "completed_stage_name": "1-GET_MSDS",
                    "completed_stage_status": "FAILED",
                    "completed_stage_status_reason": str(e.message),
                }
                mysql_run_state_detail_util.update_entry(
                    artifact_run_state_id,
                    folder_upload_table_record_data,
                )

        except Exception as e:
            self.logger.error(
                f"Artifact-Upload : {thread_id} :: {artifact_run_state_id} : Error :{str(e)}"
            )
            if mysql_session and mysql_run_state_detail_util:
                folder_upload_table_record_data = {
                    "id": artifact_run_state_id,
                    "completed_stage_name": "1-GET_MSDS",
                    "completed_stage_status": "FAILED",
                    "completed_stage_status_reason": str(e),
                }
                mysql_run_state_detail_util.update_entry(
                    artifact_run_state_id,
                    folder_upload_table_record_data,
                )

        finally:
            if mysql_session:
                mysql_session.close()

    def get_blob_urls(self, file_name, blob_storage_type):
        if blob_storage_type == BlobStorageTypes.CUSTOMER:
            return f"{constants.blob_storage_base_url}/{constants.customer_blob.base_path}/{file_name}{global_constants.file_extensions.pdf}"
        elif blob_storage_type == BlobStorageTypes.GLOBAL:
            return f"{constants.blob_storage_base_url}/{constants.global_blob.base_path}/{file_name}{global_constants.file_extensions.pdf}"
        elif blob_storage_type == BlobStorageTypes.KEYWORD_ANALYSIS:
            return f"{constants.blob_storage_base_url}/{constants.keyword_analysis_blob.base_path}/{file_name}{global_constants.file_extensions.pdf}"
        else:
            raise CommonException(501, f"{blob_storage_type} not found")

    def get_blob_file_path(self, file_name, blob_storage_type):
        if blob_storage_type == BlobStorageTypes.CUSTOMER:
            return f"/{constants.customer_blob.base_path}/{file_name}.{global_constants.file_extensions.pdf}"
        elif blob_storage_type == BlobStorageTypes.GLOBAL:
            return f"/{constants.global_blob.base_path}/{file_name}.{global_constants.file_extensions.pdf}"
        elif blob_storage_type == BlobStorageTypes.KEYWORD_ANALYSIS:
            return f"/{constants.keyword_analysis_blob.base_path}/{file_name}.{global_constants.file_extensions.pdf}"
        else:
            raise CommonException(501, f"{blob_storage_type} not found")

    def validate_file(self, file_size, content_type):
        max_file_upload_limit = 1073741824
        if file_size == 0:
            raise CommonException("Empty file")
        if content_type is None:
            raise CommonException("Unsupported file type")
        if file_size > max_file_upload_limit:
            raise CommonException("File size exceeds limit")

    def store_file_in_blob_storage(
        self, id: str, file_byte_stream: Any, blob_storage_type: BlobStorageTypes
    ):
        if blob_storage_type == BlobStorageTypes.CUSTOMER:
            file_path = self.get_blob_file_path(id, BlobStorageTypes.CUSTOMER)
        elif blob_storage_type == BlobStorageTypes.GLOBAL:
            file_path = self.get_blob_file_path(id, BlobStorageTypes.GLOBAL)
        elif blob_storage_type == BlobStorageTypes.KEYWORD_ANALYSIS:
            file_path = self.get_blob_file_path(id, BlobStorageTypes.KEYWORD_ANALYSIS)

        else:
            raise CommonException(
                f"Invalid Blob storage type : {str(blob_storage_type)}"
            )

        return self.customer_blob_storage_util.upload_file_to_blob_storage(
            type=global_constants.file_extensions.pdf,
            file_data=file_byte_stream,
            file_path=f"{file_path}/{id}",
        )

    def read_pdf_from_byte_stream(self, byte_stream):
        pdf_doc = fitz.open(global_constants.file_types.pdf, byte_stream)
        content = ""
        for page in pdf_doc:
            content += page.get_text() + "\n"

        return content

    def extract_file_text_from_keyword_analysis_result(self, identifier, no_of_pages):
        file_text = ""
        for page in range(1, no_of_pages + 1):
            page_path = f"{constants.keyword_analysis_blob.base_path}/{identifier}/page_{'{:03}'.format(page)}/page_text.txt"
            page_text = (
                self.ka_blob_storage_util.get_file_content_as_text_from_blob_storage(
                    page_path
                )
            )
            file_text += str(page_text)
        return file_text

    def extract_file_text_from_keyword_analysis_result_in_list(
        self, identifier, no_of_pages
    ) -> List[str]:
        file_text = []
        for page in range(1, no_of_pages + 1):
            page_path = f"{constants.keyword_analysis_blob.base_path}/{identifier}/page_{'{:03}'.format(page)}/page_text.txt"
            page_text = (
                self.ka_blob_storage_util.get_file_content_as_text_from_blob_storage(
                    page_path
                )
            )
            file_text.append(str(page_text))
        return file_text

    def save_artifact_data_in_database(
        self, artifact_input_data: ArtifactInputDTO
    ) -> Artifacts:
        # TODO : Add code to get upload_id, type_id, category_id
        artifact_id = str(uuid.uuid4())
        artifact = Artifacts(
            id=artifact_id,
            name=artifact_input_data.name,
            source_name=artifact_input_data.source_name,
            source_link=artifact_input_data.source_link,
            data_format=artifact_input_data.data_format,
            status=artifact_input_data.status,
            upload_status=ArtifactUploadStatus.STARTED,
            enabled=artifact_input_data.enabled,  # IF pfas yes then enebled =True else False
            organization=artifact_input_data.organization,
            trust_factor=artifact_input_data.trust_factor,
            uploaded_location=artifact_input_data.file_url,
            region=artifact_input_data.region,
            country=artifact_input_data.country,
            state=artifact_input_data.state,
            city=artifact_input_data.city,
            domain=artifact_input_data.domain,
            sub_domain=artifact_input_data.sub_domain,
            file_upload_type=artifact_input_data.file_upload_type,
            tags=(
                ",".join(artifact_input_data.tags) if artifact_input_data.tags else None
            ),
            upload_id="297e02838d7a701f018d7ce3762f017d",
            type_id="2c948a868d837c0f018d83964ba5000c",
            category_id="2c948a868d837c0f018d8393812b0008",
        )
        artifact = self.artifact_repo.save_and_flush(artifact)
        return artifact

    def update_artifact_status(
        self, artifact: Artifacts, upload_status: ArtifactUploadStatus
    ) -> Artifacts:
        artifact.upload_status = upload_status
        artifact = self.artifact_repo.save_and_flush(artifact)
        return artifact

    def save_msds(
        self,
        msds_analysis: MSDSAnalysis,
        artifact: Artifacts,
    ) -> GlobalNode:
        try:
            thread_id = ThreadingTool.get_thread_id()
            if artifact.upload_status == ArtifactUploadStatus.STARTED:
                # Check if material already ingested
                self.check_if_material_already_ingested(msds_analysis)

                # Add manufacturer if already not exists
                manufacturer = self.save_manufacturer(msds_analysis)
                self.logger.info(
                    f"Artifact-Upload : {thread_id} :: {artifact.id} : Saved manufacturer in database : {manufacturer.__dict__}"
                )

                # Add material
                material = self.save_material(msds_analysis, manufacturer)
                self.logger.info(
                    f"Artifact-Upload : {thread_id} :: {artifact.id} : Saved material in database : {material.__dict__}",
                )

                # Save chemicals of material and update PFAS status
                material_pfas_status = (
                    self.save_chemicals_of_material_and_update_pfas_status(
                        msds_analysis, manufacturer, material
                    )
                )

                artifact.enabled = material_pfas_status != PfasStatus.PENDING
                # artifact.set_updated_base_data()
                self.artifact_repo.save(artifact)

                self.logger.info(
                    f"Artifact-Upload : {thread_id} :: {artifact.id} : Updated artifact in database : {artifact.__dict__}"
                )

                # Save document
                document_metadata = self.save_document_metadata(artifact)
                self.logger.info(
                    f"Artifact-Upload : {thread_id} :: {artifact.id} : Saved document_metadata in database : {document_metadata.__dict__}"
                )

                # Get and save material to document mapping
                material_to_document_mapping = self.get_material_to_document_mapping(
                    document_metadata, material
                )
                material_to_document_mapping = (
                    self.material_to_document_mapping_repo.save(
                        material_to_document_mapping
                    )
                )
                self.logger.info(
                    f"Artifact-Upload : {thread_id} :: {artifact.id} : Saved material_to_document_mapping in database : {material_to_document_mapping.__dict__}"
                )

                msds_analysis.material_id = material.id

                # if artifact.upload_status == ArtifactUploadStatus.STARTED:
                #     self.upload_artifacts(
                #         artifact.name,
                #         artifact,
                #         msds_analysis.analysis_identifier,
                #     )

                self.session.commit()
                self.logger.info("Committed database changes")
                return material

            # This is for review
            else:
                # Update the materials status and chemical status
                optional_material = self.global_node_repo.find_by_id(
                    msds_analysis.material_id
                )
                if optional_material:
                    material_by_id = optional_material
                    material_by_id.pfas_status = msds_analysis.pfas_status
                    material_by_id.pfas_information_source = (
                        msds_analysis.pfas_information_source
                    )
                    material_hierarchy = self.node_hierarchy_repo.find_all_by_parent_id(
                        material_by_id.id
                    )
                    for hierarchy in material_hierarchy:
                        chemical_node = hierarchy.child_node_id
                        chemicals_open_ai_response = next(
                            (
                                chem
                                for chem in msds_analysis.chemicals
                                if chem.chemical_name.lower()
                                == chemical_node.name.lower()
                            ),
                            None,
                        )
                        if chemicals_open_ai_response:
                            self.determine_and_set_the_chemical_pfas_info_source_and_status(
                                chemicals_open_ai_response, chemical_node
                            )
                        saved_chemical = self.global_node_repo.save(chemical_node)

                        # Get all materials having this chemical
                        all_materials_having_chemical = (
                            self.global_node_repo.find_materials_by_chemical_id(
                                saved_chemical.id
                            )
                        )
                        # Iterate over all materials and update the PFAS status
                        for material_node in all_materials_having_chemical:
                            self.update_the_material_based_on_chemical_status_and_source(
                                material_node
                            )

                    self.determine_and_update_material_pfas_status(
                        msds_analysis.chemicals, material_by_id
                    )

                return ResponseEntityDTO("SUCCESS", msds_analysis, 1)

        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error while saving msds in database :{str(e)}")
            raise e

    def get_artifact_file_properties(self, file_upload_type, file):
        file_name, file_type, file_size, file_byte_stream = None, None, None, None

        match file_upload_type:
            case "LOCAL":
                file_name = file.name
                file_size = file.size
                file_type = file.content_type
                file_byte_stream = file.content

            case "BLOB_STORAGE":
                file_properties = self.internal_blob_storage_util.get_file_properties(
                    file
                )
                file_byte_stream = (
                    self.internal_blob_storage_util.get_file_as_bytes_from_blob_storage(
                        file
                    )
                )
                file_name = file_properties.name
                file_size = file_properties.size
                file_type = file_properties.content_settings.content_type

            case "SHAREPOINT":
                file_properties = self.asyncio_event_loop.run_until_complete(
                    self.sharepoint_util.get_file_properties(file)
                )
                file_byte_stream = self.asyncio_event_loop.run_until_complete(
                    self.sharepoint_util.read_file_from_share_point(file)
                )

                file_name = file_properties.name
                file_size = file_properties.size
                file_type = (
                    file_properties.file.mime_type if file_properties.file else None
                )

            case _:
                raise CommonException(
                    f"Unsupported file upload type : {str(file_upload_type)}"
                )

        return file_name, file_type, file_size, file_byte_stream

    def analyze_msds(self, file, artifact: Artifacts) -> MSDSAnalysis:
        file_name, file_type, file_size, file_byte_stream = (
            self.get_artifact_file_properties(artifact.file_upload_type, file)
        )

        # Upload msds pdf file to global system blob storage
        self.store_file_in_blob_storage(
            artifact.id, file_byte_stream, BlobStorageTypes.GLOBAL
        )

        # Upload msds pdf file to keyword-anlaysis blob storage
        ka_file_uri = self.store_file_in_blob_storage(
            artifact.id,
            file_byte_stream,
            BlobStorageTypes.KEYWORD_ANALYSIS,
        )

        # TODO : Call entity-extracter service, instead of usign openai for analysis
        return self.get_msds_analysis(ka_file_uri)

    def add_artifact(
        self,
        artifact_input_data: ArtifactInputDTO,
    ) -> Artifacts:
        file_name, file_type, file_size, file_byte_stream = (
            self.get_artifact_file_properties(
                artifact_input_data.file_upload_type, artifact_input_data.file_url
            )
        )

        self.validate_file(file_size, file_type)

        # Initialize artifact and save in database
        artifact = self.save_artifact_data_in_database(artifact_input_data)

        # Upload msds pdf file to customer blob storage
        self.store_file_in_blob_storage(
            artifact.id, file_byte_stream, BlobStorageTypes.CUSTOMER
        )

        return artifact

    def get_msds_analysis(self, file_uri) -> MSDSAnalysis:
        keyword_analysis_identifier, total_pages = (
            self.file_analysis_service.process_queue_item(
                queue_item=None,
                file_uri=file_uri,
                input_file_source="blob",
                search_scope="local",
                local_keywords=[],
                force=True,
                if_internal_service_call=True,
                thread_id=-1,
            )
        )
        if not keyword_analysis_identifier or not total_pages:
            CommonException("Not able to extract text using keyword analysis")

        pdf_text_content = self.extract_file_text_from_keyword_analysis_result(
            keyword_analysis_identifier, total_pages
        )

        msds_analysis = self.analyze_msds_using_openai(
            pdf_text_content, keyword_analysis_identifier
        )
        return msds_analysis

    def combine_material_name(self, material_name, product_no, upc_number):
        SPACE = " "
        OPEN_BRACKET = "("
        CLOSE_BRACKET = ")"
        EMPTY_STRING = ""

        product_no_part = (
            f"{SPACE}{OPEN_BRACKET}{product_no}{CLOSE_BRACKET}"
            if product_no and product_no.strip()
            else EMPTY_STRING
        )
        upc_number_part = (
            f"{SPACE}{OPEN_BRACKET}{upc_number}{CLOSE_BRACKET}"
            if upc_number and upc_number.strip()
            else EMPTY_STRING
        )

        return f"{material_name}{product_no_part}{upc_number_part}"

    def get_embeddings(self, content: str) -> List[float]:
        try:
            chosen_language_model = "OPENAI"
            if chosen_language_model == "OPENAI":
                result = self.openai_util.get_embeddings(content)
            else:
                raise LanguageModelException(
                    f"Unsupported model type: {chosen_language_model}"
                )
            return result
        except Exception as e:
            self.logger.error(e)
            raise LanguageModelException("Unable to get embedding")

    # MSDS Analysis Function
    def analyze_msds_using_openai(
        self,
        pdf_text_content: str,
        keyword_analysis_identifier: str,
    ) -> MSDSAnalysis:
        try:
            prompt = constants.msds_analysis_system_prompt.replace(
                "__CONTENT__", pdf_text_content
            )
            # Simulate OpenAI call
            openai_response = self.openai_util.complete_chat_turbo(content=prompt)
            updated_response = openai_response.replace("json", "").replace("```", "")

            # Parse JSON response
            parsed_mds_data = json.loads(updated_response)
            parsed_mds_data["chemicals"] = [
                Chemical(**chem) for chem in parsed_mds_data["chemicals"]
            ]
            msds_response = MSDSAnalysis(**parsed_mds_data)

            # Process data
            msds_response.material_name = self.combine_material_name(
                msds_response.material_name,
                msds_response.product_number,
                msds_response.upc_number,
            )
            msds_response.analysis_identifier = keyword_analysis_identifier

            # Distinct chemicals
            distinct_chemicals = {
                (chem.chemical_name): chem for chem in msds_response.chemicals
            }
            msds_response.chemicals = list(distinct_chemicals.values())

            # Additional checks
            if not msds_response.material_name:
                raise LanguageModelException(
                    204, "Unable to extract material from MSDS, please try again."
                )
            if not msds_response.chemicals:
                raise LanguageModelException(
                    204,
                    f"Ingredients not found for material: {msds_response.material_name}",
                )
            return msds_response

        except (json.JSONDecodeError, LanguageModelException) as e:
            self.logger.error(e)
            raise CommonException(
                500, "Unable to analyse file content, please try again."
            )
        except CommonException as e:
            self.logger.error(e)
            raise CommonException(e.status_code, e.message)
        except Exception as e:
            self.logger.error(e)
            raise CommonException(
                500, "Unable to extract material from MSDS, please try again."
            )

    def get_parent_pfas_resolution(
        ingredients_pfas_status: List[PFASResolution],
    ) -> PFASResolution:
        parent_pfas_resolution = PFASResolution()

        """
        Get pfas status of material , it can be pending, yes, no
        """
        has_pfas = False
        has_pending = False
        # Check each resolution for PFAS status
        for child_pfas_resolution in ingredients_pfas_status:
            # if any chemical is found with pfas yes then the material will be also pfas = yes
            if child_pfas_resolution.pfas_status == PfasStatus.YES:
                has_pfas = True
                break
            elif child_pfas_resolution.pfas_status == PfasStatus.PENDING:
                has_pending = True

        # Assign the PFAS Status
        if has_pfas:
            parent_pfas_resolution.pfas_status = PfasStatus.YES
        elif not has_pending:
            parent_pfas_resolution.pfas_status = PfasStatus.NO
        else:
            parent_pfas_resolution.pfas_status = PfasStatus.PENDING

        """
        Determine the pfas information source based on the given preferences as per the pfas status
        Iterate over the preferences and if the preference is found with count > 0 set the information source with that preference
        """
        # Determine the order of preference for PFAS information sources
        # TODO : Check the presence list again with latest code
        if parent_pfas_resolution.pfas_status == PfasStatus.PENDING:
            pfas_order_of_preference = [
                PfasInformationSource.OECD,
                PfasInformationSource.VAI,
                PfasInformationSource.MANUAL,
            ]
        else:
            pfas_order_of_preference = [
                PfasInformationSource.VAI,
                PfasInformationSource.OECD,
                PfasInformationSource.MANUAL,
            ]

        # Count occurrences of each PFAS information source
        count_information_source = Counter(
            res.pfas_information_source
            for res in ingredients_pfas_status
            if res.pfas_status == parent_pfas_resolution.pfas_status
        )

        # Assign the most preferred information source
        for source in pfas_order_of_preference:
            count = count_information_source.get(source, 0)
            if count > 0:
                parent_pfas_resolution.pfas_information_source = source
                break

        return parent_pfas_resolution

    def get_pfas_status_from_tag(self, pfas_tag: str) -> PfasStatus:
        if pfas_tag == OpenAiPfasStatus.PFAS.value:
            return PfasStatus.YES
        elif pfas_tag == OpenAiPfasStatus.NO_PFAS.value:
            return PfasStatus.NO
        else:
            return PfasStatus.PENDING

    def get_material_pfas_resolution(
        self, chemicals: List[ChemicalsOpenAiResponse]
    ) -> PFASResolution:
        child_pfas_resolutions = [
            PFASResolution(
                self.get_pfas_status_from_tag(chemical.tag),
                chemical.pfas_information_source,
            )
            for chemical in chemicals
        ]
        return self.get_parent_pfas_resolution(child_pfas_resolutions)

    def determine_and_update_material_pfas_status(
        self, chemicals: ChemicalsOpenAiResponse, material: GlobalNode
    ):
        # Update PFAS status other than PFAS and no PFAS as pending for potential PFAS
        parent_pfas_resolution = self.get_material_pfas_resolution(chemicals)
        material.pfas_status = parent_pfas_resolution.pfas_status
        material.pfas_information_source = (
            parent_pfas_resolution.pfas_information_source
        )

        # material.set_updated_base_data()
        self.global_node_repo.save(material)
        return material.pfas_status

    def embed_and_upsert_document(self, artifacts_documents, tenant_id=1):
        try:
            vector_upsert = []
            for text in artifacts_documents:
                embedded_vector = self.get_embeddings(text)
                artifacts_vector = {
                    "id": str(uuid.uuid4()),
                    "text": text,
                    "embedding": embedded_vector,
                }
                vector_upsert.append(artifacts_vector)

                # TODO : Upsert embedding into pg_vector
                # if (len(vector_upsert.vectors) % vector_db_upsert_limit == 0) or (
                #     document_count == len(artifacts_documents) - 1
                # ):
                #     vector_store = VectorStore(
                #         gateway_repo, tenant_id, vector_store_artifact_url
                #     )
                #     vector_store.upsert(vector_upsert, vector_store_vector_upsert)
                #     vector_upsert.vectors = []
                # time.sleep(embedding_wait_time)
        except Exception as e:
            raise CommonException("501", "Unable to embed and upsert")

    # Upload embedding to pg vector
    def upload_artifacts(self, file_name, artifact: Artifacts):
        try:
            artifact = self.update_artifact_status(
                artifact, ArtifactUploadStatus.CHUNKING
            )

            file_uri = self.get_blob_urls(artifact.id, BlobStorageTypes.CUSTOMER)

            keyword_analysis_identifier, total_pages = (
                self.file_analysis_service.process_queue_item(
                    queue_item=None,
                    file_uri=file_uri,
                    input_file_source="blob",
                    search_scope="local",
                    local_keywords=[],
                    force=True,
                    if_internal_service_call=True,
                    thread_id=-1,
                )
            )

            artifacts_documents = (
                self.extract_file_text_from_keyword_analysis_result_in_list(
                    keyword_analysis_identifier, total_pages
                )
            )

            self.update_artifact_status(artifact, ArtifactUploadStatus.EMBEDDING)
            self.embed_and_upsert_document(artifacts_documents)
            self.update_artifact_status(artifact, ArtifactUploadStatus.UPLOADED)

        except Exception as e:
            # TODO : Add code for deleting artifacts, vectors
            # self.delete_artifact_global_metadata(artifact)
            # self.artifact_repository.delete_by_id(artifact.id)
            # self.delete_artifact_blob_and_vectors(artifact)
            pass

    def check_if_material_already_ingested(self, parsed_msds_data: MSDSAnalysis):
        material_node = (
            self.global_node_repo.find_material_by_name_and_manufacturer_name(
                parsed_msds_data.material_name, parsed_msds_data.manufacturer_name
            )
        )
        if material_node:
            raise CommonException(
                "MATERIAL_ALREADY_INGESTED",
                "ArtifactFolderCrawler",
            )

    def save_manufacturer(self, msds_analysis: MSDSAnalysis):
        manufacturer = self.manufacturer_repo.find_by_name(
            msds_analysis.manufacturer_name
        )
        if not manufacturer:
            manufacturer = Manufacturer(
                id=str(uuid.uuid4()),
                name=msds_analysis.manufacturer_name,
                address=msds_analysis.manufacturer_address,
                postal_code=msds_analysis.manufacturer_postal_code,
                city=msds_analysis.manufacturer_city,
                state=msds_analysis.manufacturer_state,
                country=msds_analysis.manufacturer_country,
                region=msds_analysis.manufacturer_region,
            )
            # manufacturer.set_base_data()
            self.manufacturer_repo.save(manufacturer)
        return manufacturer

    def save_material(
        self,
        msds_analysis: MSDSAnalysis,
        saved_manufacturer: Manufacturer,
    ):
        material = GlobalNode(
            id=str(uuid.uuid4()),
            name=msds_analysis.material_name,
            manufacturer_id=saved_manufacturer.id,
            node_type=GlobalNodeTypes.MATERIAL,
            pfas_status=PfasStatus.PENDING,
            pfas_information_source=PfasInformationSource.NONE,
            cas_number=None,
        )
        # material.set_base_data()
        return self.global_node_repo.save(material)

    def get_chemical_node(
        self,
        chemicals_openai_response: ChemicalsOpenAiResponse,
        manufacturer: Manufacturer,
    ) -> GlobalNode:
        # Determine the PFAS status of the chemical
        status = self.get_pfas_status_from_tag(chemicals_openai_response.tag)

        cas_number = (
            chemicals_openai_response.cas_no.strip()
            if chemicals_openai_response.cas_no
            else None
        )

        # Check if the chemical is already present
        chemical = None

        # If cas_number is present get chemical by cas_number and manufacturer id
        if cas_number:
            chemical = (
                self.global_node_repo.find_chemical_by_cas_number_and_manufacturer_id(
                    cas_number, manufacturer.id
                )
            )
            if chemical:
                chemical = chemical[0]  # Get the first result

        # If chemical is not found by cas_number then find by chemical_name and manufacturer id
        if not chemical:
            chemical = self.global_node_repo.find_chemical_by_name_and_manufacturer_id(
                chemicals_openai_response.chemical_name, manufacturer.id
            )
            if chemical:
                chemical = chemical[0]  # Get the first result

        # If chemical is not found add a new entry for chemical
        if not chemical:
            # Create a new GlobalNode object representing the chemical
            chemical = GlobalNode(
                id=str(uuid.uuid4()),
                name=chemicals_openai_response.chemical_name,
                description=chemicals_openai_response.chemical_name,
                manufacturer=manufacturer,
                node_type=GlobalNodeTypes.CHEMICAL,
                pfas_status=status,
                pfas_information_source=chemicals_openai_response.pfas_information_source,
                cas_number=cas_number,
            )
            # chemical.set_base_data()
        else:
            # Determine the information source and the PFAS status according to source from existing and new
            chemical = self.determine_and_set_the_chemical_pfas_info_source_and_status(
                chemicals_openai_response, chemical
            )
            chemical.cas_number = cas_number
            # chemical.set_updated_base_data()

        return chemical

    def get_node_hierarchy(
        self, node_hierarchy_composite_key: GlobalNodeHierarchyCompositeKey, composition
    ):

        node_hierarchy = self.node_hierarchy_repo.find_all_by_parent_and_child_id(
            node_hierarchy_composite_key.parent_node_id,
            node_hierarchy_composite_key.child_node_id,
        )

        if node_hierarchy is None:
            node_hierarchy = GlobalNodeHierarchy(
                parent_node_id=node_hierarchy_composite_key.parent_node_id,
                child_node_id=node_hierarchy_composite_key.child_node_id,
                chemical_weight_percent=composition,
            )
            # node_hierarchy.set_base_data()
        else:
            node_hierarchy.chemical_weight_percent = composition
            # node_hierarchy.set_updated_base_data()

        return node_hierarchy

    def save_chemicals_of_material_and_update_pfas_status(
        self,
        msds_analysis: MSDSAnalysis,
        manufacturer: Manufacturer,
        material: GlobalNode,
    ):
        final_pfas_status = PfasStatus.PENDING
        for chemical_openai_response in msds_analysis.chemicals:
            # Save chemical
            chemical = self.get_chemical_node(chemical_openai_response, manufacturer)
            saved_chemical = self.global_node_repo.save(chemical)

            # Save material[parent]-chemical[child] hierarchy in node_hierarchy table
            node_hierarchy_composite_key = GlobalNodeHierarchyCompositeKey(
                parent_node_id=material.id, child_node_id=saved_chemical.id
            )
            node_hierarchy = self.get_node_hierarchy(
                node_hierarchy_composite_key, chemical_openai_response.composition
            )
            node_hierarchy = self.node_hierarchy_repo.save(node_hierarchy)

            # TODO : Need to check this logic with tushar
            ## Update the status of all the parents materials
            all_materials_having_chemical = (
                self.global_node_repo.find_materials_by_chemical_id(saved_chemical.id)
            )
            for material_node in all_materials_having_chemical:
                parent_pfas_resolution = (
                    self.update_the_material_based_on_chemical_status_and_source(
                        material_node
                    )
                )

                # Set result for current material
                if material_node.id == material.id:
                    final_pfas_status = parent_pfas_resolution.pfas_status

        return final_pfas_status

    def save_document_metadata(self, artifacts: Artifacts) -> DocumentMetadata:
        document_metadata = DocumentMetadata(
            id=str(uuid.uuid4()),
            name=artifacts.name,
            locator=self.get_blob_urls(artifacts.id, BlobStorageTypes.CUSTOMER),
            document_category=artifacts.file_upload_type,
            document_type="MSDS",
        )
        # document_metadata.set_base_data()
        return self.document_metadata_repo.save(document_metadata)

    def get_material_to_document_mapping(
        self, document_metadata: DocumentMetadata, material: GlobalNode
    ) -> MaterialToDocumentMapping:
        material_to_document_mapping_composite_key = MaterialToDocumentCompositeKey(
            document_id=document_metadata.id, material_id=material.id
        )
        material_to_document_mapping = MaterialToDocumentMapping(
            document_id=material_to_document_mapping_composite_key.document_id,
            material_id=material_to_document_mapping_composite_key.material_id,
        )
        # material_to_document_mapping.set_base_data()
        return material_to_document_mapping

    def determine_final_status(
        self, existing_source, new_source, existing_pfas_status, new_pfas_status
    ):
        if (
            (
                existing_source == PfasInformationSource.OECD
                and new_source == PfasInformationSource.VAI
            )
            or (
                existing_source == PfasInformationSource.VAI
                and new_source == PfasInformationSource.VAI
            )
            or (
                existing_source == PfasInformationSource.NONE
                and new_source == PfasInformationSource.VAI
            )
            or (
                existing_source == PfasInformationSource.VAI
                and new_source == PfasInformationSource.MANUAL
            )
            or (
                existing_source == PfasInformationSource.NONE
                and new_source == PfasInformationSource.MANUAL
            )
            or (
                existing_source == PfasInformationSource.VAI
                and new_source == PfasInformationSource.OECD
            )
            or (
                existing_source == PfasInformationSource.NONE
                and new_source == PfasInformationSource.OECD
            )
        ):
            return new_pfas_status
        return existing_pfas_status

    def get_transition_map_for_pfas_information_source(
        self,
    ):
        transition_map = {
            "OPENAI" + "_" + "OPENAI": PfasInformationSource.VAI,
            "MANUAL" + "_" + "OPENAI": PfasInformationSource.MANUAL,
            "OECD" + "_" + "OPENAI": PfasInformationSource.OECD,
            "NONE" + "_" + "OPENAI": PfasInformationSource.VAI,
            "OPENAI" + "_" + "MANUAL": PfasInformationSource.MANUAL,
            "MANUAL" + "_" + "MANUAL": PfasInformationSource.MANUAL,
            "OECD" + "_" + "MANUAL": None,  # Not possible
            "NONE" + "_" + "MANUAL": PfasInformationSource.MANUAL,
            "OPENAI" + "_" + "OECD": PfasInformationSource.OECD,
            "MANUAL" + "_" + "OECD": None,  # Not possible
            "OECD" + "_" + "OECD": PfasInformationSource.OECD,
            "NONE" + "_" + "OECD": PfasInformationSource.OECD,
            "OPENAI" + "_" + "NONE": PfasInformationSource.VAI,
            "MANUAL" + "_" + "NONE": PfasInformationSource.MANUAL,
            "OECD" + "_" + "NONE": PfasInformationSource.OECD,
            "NONE" + "_" + "NONE": PfasInformationSource.NONE,
        }
        return transition_map

    def determine_final_source(
        self, existing_source: PfasInformationSource, new_source: PfasInformationSource
    ):
        transition_map = self.get_transition_map_for_pfas_information_source()
        key = existing_source.value + "_" + new_source.value
        return transition_map.get(key)

    def determine_and_set_the_chemical_pfas_info_source_and_status(
        self, chemicals_open_ai_response: ChemicalsOpenAiResponse, chemical: GlobalNode
    ) -> GlobalNode:
        final_source = self.determine_final_source(
            chemical.pfas_information_source,
            chemicals_open_ai_response.pfas_information_source,
        )
        if final_source is None:
            raise CommonException(
                "TRANSITION_FROM_0_TO_1_IS_NOT_POSSIBLE",
                "ArtifactFolderCrawler",
            )

        chemical.pfas_status = self.determine_final_status(
            chemical.pfas_information_source,
            chemicals_open_ai_response.pfas_information_source,
            chemical.pfas_status,
            self.get_pfas_status_from_tag(chemicals_open_ai_response.tag),
        )
        chemical.pfas_information_source = final_source
        return chemical

    def update_the_material_based_on_chemical_status_and_source(
        self,
        material_node: GlobalNode,
    ) -> PFASResolution:
        all_chemicals_for_material = self.global_node_repo.find_chemicals_by_material(
            material_node.id
        )
        """
        Get pfas status of all chemicals associated with the material and decide the status of material accorrding to status of chemicals
        """
        child_pfas_resolution = [
            PFASResolution(
                mat_chemical.pfas_status, mat_chemical.pfas_information_source
            )
            for mat_chemical in all_chemicals_for_material
        ]
        parent_pfas_resolution = self.get_parent_pfas_resolution(child_pfas_resolution)
        material_node.pfas_status = parent_pfas_resolution.pfas_status
        material_node.pfas_information_source = (
            parent_pfas_resolution.pfas_information_source
        )
        # material_node.set_updated_base_data()
        self.global_node_repo.save(material_node)
        return parent_pfas_resolution
