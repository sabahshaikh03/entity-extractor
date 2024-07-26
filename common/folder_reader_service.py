import json
from utils.sharepoint import SharePoint
from connectors.sharepoint_connector import SharePointConnector
from utils.azure_queue import AzureQueue
from connectors.mysql_connector import MySQLConnector
from utils.mysql import MySQL
import uuid
from common.models.folder_upload import FolderUpload
from logging import Logger
from app.modules.artifact_ingestor.models.artifact_upload_run_state_details import (
    ArtifactUploadRunStateDetails,
)
import time
from utils.exceptions import MissingRequiredDetailsError
from azure.storage.queue import QueueMessage
from sqlalchemy.orm import Session
from common.dto.folder_reader_input_dto import FolderReaderInputDTO
from utils.threading_tools import ThreadingTool
from utils.task_visiblity_controller import TaskVisibilityController


class FolderReader:
    def __init__(self, logger: Logger, asyncio_event_loop=None):
        self.logger = logger
        self.asyncio_event_loop = asyncio_event_loop
        self.sharepoint_util = self._init_sharepoint_util()
        self.azure_queue_util = AzureQueue()

    def _init_sharepoint_util(self):
        share_point_connector = SharePointConnector()
        sharepoint_client = share_point_connector.get_client()
        return SharePoint(sharepoint_client)

    def add_file_in_queue(
        self, file_path, artifact_upload_run_state_id
    ) -> QueueMessage:
        queue_message = {
            "message_type": "msds-artifact-upload",
            "data": {
                "full_path": file_path,
                "artifact_upload_run_state_id": artifact_upload_run_state_id,
            },
        }
        return self.azure_queue_util.enqueue(queue_message)

    def add_entry_in_artifact_upload_run_state_details_table(
        self,
        id,
        folder_id,
        full_path,
        message_id,
        mysql_session: Session,
    ):
        mysql_util = MySQL(
            logger=self.logger,
            session=mysql_session,
            table=ArtifactUploadRunStateDetails,
        )
        current_timestamp = int(time.time())
        data = {
            "id": id,
            "folder_upload_id": folder_id,
            "full_path": full_path,
            "message_id": message_id,
            "queue_name": "keywordanalysisqueue",
            "folder_upload_type": "FOLDER",
            "completed_stage_name": "1-QUEUING",
            "completed_stage_status": "SUCCESS",
            "created_at": current_timestamp,
            "updated_at": current_timestamp,
        }
        mysql_util.add_entry(data)

    def get_running_count_and_next_page_link_from_database(
        self, folder_upload_id, mysql_folder_upload_util
    ):
        data = mysql_folder_upload_util.get_entry_by_primary_key(folder_upload_id)
        if data is None:
            raise MissingRequiredDetailsError("folder_upload_id is invalid")
        return (
            0 if data.running_count is None else int(data.running_count)
        ), data.next_page_link

    def fetch_files_from_sharepoint(self, folder_location, next_page_link):
        return self.asyncio_event_loop.run_until_complete(
            self.sharepoint_util.get_files_from_folder_in_batch(
                root_folder_uri=(folder_location if next_page_link is None else None),
                page_link=next_page_link,
                batch_size=200,
            )
        )

    def process_folder(self, folder_reader_input_data: FolderReaderInputDTO):
        try:
            thread_id = ThreadingTool.get_thread_id()
            # Logging
            self.logger.info(
                f"Folder-Reader : {thread_id} :: {folder_reader_input_data.folder_upload_id} : Started"
            )
            # Create mysql session
            mysql_session = MySQLConnector().get_session()
            mysql_folder_upload_util = MySQL(
                logger=self.logger, session=mysql_session, table=FolderUpload
            )

            self.logger.info(
                f"Folder-Reader : {thread_id} :: {folder_reader_input_data.folder_upload_id} : Connected to MySQL"
            )

            # Get running count and next page link from folder upload table if the folder is already processed
            running_count, next_page_link = (
                self.get_running_count_and_next_page_link_from_database(
                    folder_reader_input_data.folder_upload_id, mysql_folder_upload_util
                )
            )

            while True:
                # Get files from sharepoint using folder uri or next page link
                files, next_page_link = self.fetch_files_from_sharepoint(
                    folder_reader_input_data.folder_location, next_page_link
                )
                running_count += len(files)

                # Add files to queue and add entry in artifact_upload_run_state_details table
                for file_path in files:
                    artifact_upload_run_state_id = str(uuid.uuid1()).replace("-", "")
                    message = self.add_file_in_queue(
                        file_path, artifact_upload_run_state_id
                    )

                    self.add_entry_in_artifact_upload_run_state_details_table(
                        artifact_upload_run_state_id,
                        folder_reader_input_data.folder_upload_id,
                        file_path,
                        message.id,
                        mysql_session,
                    )

                # Update folder_upload table
                folder_upload_table_record_data = {
                    "id": folder_reader_input_data.folder_upload_id,
                    "location_type": folder_reader_input_data.location_type,
                    "folder_location": folder_reader_input_data.folder_location,
                    "artifact_type": folder_reader_input_data.artifact_type,
                    "status": "PROCESSING",
                    "total_count": (
                        running_count if next_page_link is None else 0
                    ),  # Update the total count after total files fetched
                    "running_count": running_count,
                    "next_page_link": next_page_link,
                }

                mysql_folder_upload_util.update_entry(
                    folder_reader_input_data.folder_upload_id,
                    folder_upload_table_record_data,
                )

                # If the execution time reaches visibility time then extend the visibility time
                TaskVisibilityController.check_and_extend_visibility_timeout()

                # Break the loop if there are no more files to fetch
                if next_page_link is None:
                    break

            self.logger.info(
                f"Folder-Reader : {thread_id} :: {folder_reader_input_data.folder_upload_id} : added {len(files)} artifact files in queue"
            )

        except Exception as e:
            self.logger.error(
                f"Folder-Reader : {thread_id} :: {folder_reader_input_data.folder_upload_id} : Error : {str(e)}"
            )
            folder_upload_table_record_data = {
                "id": folder_reader_input_data.folder_upload_id,
                "status": "FAILED",
            }
            mysql_folder_upload_util.update_entry(
                folder_reader_input_data.folder_upload_id,
                folder_upload_table_record_data,
            )

        finally:
            if mysql_session:
                mysql_session.close()
