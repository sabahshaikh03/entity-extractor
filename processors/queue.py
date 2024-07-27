import time
import json
import asyncio
from global_constants import GlobalConstants
from utils.azure_queue import AzureQueue
from utils.exceptions import MaxProcessingTimeExceededException
from utils.exceptions import MissingRequiredDetailsError
from utils.encoding import Encoding
from logging import Logger
from app.modules.keyword_analysis.services.handle_queue_item import (
    HandleQueueItem as KeywordAnalysisQueueHandler,
)
from common.folder_reader_service import FolderReader
from app.modules.artifact_ingestor.services.artifact_ingestor_service import (
    ArtifactIngestorService,
)
from app.modules.artifact_ingestor.dto.artifact_ingestor_input_dto import (
    ArtifactIngestorInputDTO,
)

from common.dto.folder_reader_input_dto import (
    FolderReaderInputDTO,
)
from utils.threading_tools import ThreadingTool
from azure.storage.queue import QueueMessage
from utils.task_visiblity_controller import TaskVisibilityController

global_constants = GlobalConstants
azure_queue_util = AzureQueue()


class QueueProcessor:
    def __init__(self, logger: Logger):
        self.logger = logger
        asyncio_event_loop = asyncio.new_event_loop()
        self.encoder = Encoding()
        self.keyword_analysis_handle_queue_item = KeywordAnalysisQueueHandler(logger)
        self.folder_reader_service = FolderReader(logger, asyncio_event_loop)
        self.artifact_ingestor_service = ArtifactIngestorService(
            logger, asyncio_event_loop
        )

    def validate_data(self, data, required_fields):
        if data is None:
            raise MissingRequiredDetailsError("Missing required data")
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise MissingRequiredDetailsError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )
        return True

    def process_keyword_analysis(self, queue_item: QueueMessage):
        try:
            thread_id = ThreadingTool.get_thread_id()
            # Extract api parameters from queue item and process it
            file_uri, processed_queue_item = (
                self.keyword_analysis_handle_queue_item.extract_api_parameters_and_process_queue_item(
                    queue_item, thread_id
                )
            )
            if file_uri and processed_queue_item:
                base64_encoded_file_uri = self.encoder.encode_data(file_uri)
                # Delete queue item after processing
                azure_queue_util.delete_queue_item(processed_queue_item)
                self.logger.info(
                    f"Thread : {thread_id} :: Queue item deleted for {base64_encoded_file_uri} [{file_uri}]"
                )
        # If max processing time is reached, the file will processed later
        except MaxProcessingTimeExceededException:
            pass

    def process_folder_scan(self, queue_item: QueueMessage):
        try:
            thread_id = ThreadingTool.get_thread_id()
            TaskVisibilityController.set_queue_item(queue_item)

            required_fields = [
                "artifact_type",
                "location_type",
                "folder_location",
                "folder_upload_id",
            ]
            queue_content = json.loads(queue_item.content)
            data = queue_content.get("data")
            self.validate_data(data, required_fields)

            artifact_type = data.get("artifact_type")
            location_type = data.get("location_type")
            folder_location = data.get("folder_location")
            folder_upload_id = data.get("folder_upload_id")

            folder_reader_input_data = FolderReaderInputDTO(
                artifact_type=artifact_type,
                location_type=location_type,
                folder_location=folder_location,
                folder_upload_id=folder_upload_id,
            )

            self.folder_reader_service.process_folder(folder_reader_input_data)

            queue_item = TaskVisibilityController.get_queue_item()
            azure_queue_util.delete_queue_item(queue_item)

        # If max processing time is reached, the file will processed later
        except MaxProcessingTimeExceededException:
            pass

        except (MissingRequiredDetailsError, json.JSONDecodeError) as e:
            self.logger.exception(f"Thread : {thread_id} :: Exception :{str(e)}")
            azure_queue_util.delete_queue_item(queue_item)

        except Exception as e:
            self.logger.error(f"Thread : {thread_id} :: Error :{str(e)}")

        finally:
            TaskVisibilityController.clear_data()

    def process_artifact_upload(self, queue_item: QueueMessage):
        try:
            thread_id = ThreadingTool.get_thread_id()
            TaskVisibilityController.set_queue_item(queue_item)

            required_fields = [
                "full_path",
                "artifact_upload_run_state_id",
            ]
            queue_content = json.loads(queue_item.content)
            data = queue_content.get("data")
            self.validate_data(data, required_fields)

            artifact_file_url = data.get("full_path")
            artifact_upload_run_state_id = data.get("artifact_upload_run_state_id")

            data = ArtifactIngestorInputDTO(
                artifact_file_url=artifact_file_url,
                artifact_upload_run_state_id=artifact_upload_run_state_id,
            )
            self.artifact_ingestor_service.ingest_artifact(data)
            queue_item = TaskVisibilityController.get_queue_item()
            azure_queue_util.delete_queue_item(queue_item)

        # If max processing time is reached, the file will processed later
        except MaxProcessingTimeExceededException:
            pass

        except (MissingRequiredDetailsError, json.JSONDecodeError) as e:
            self.logger.exception(f"Thread : {thread_id} :: Exception :{str(e)}")
            azure_queue_util.delete_queue_item(queue_item)

        except Exception as e:
            self.logger.exception(f"Thread : {thread_id} :: Error :{str(e)}")

        finally:
            TaskVisibilityController.clear_data()

    def process_waiting_queue_items(self, thread_id: int):
        thread_id = ThreadingTool.get_thread_id()
        self.logger.info(f"Thread : {thread_id} :: Started...")
        while True:
            try:
                # Get queue item from azure queue
                queue_item = azure_queue_util.dequeue(
                    visiblity_timeout=global_constants.queue_visiblity_time
                )

                # If queue is empty, wait for 5 seconds and continue
                if queue_item is None:
                    time.sleep(5)
                    continue

                self.logger.info(
                    f"Thread : {thread_id} :: Items in queue : {azure_queue_util.get_queue_length()}."
                )
                self.logger.info(
                    f"Thread : {thread_id} :: Queue item : {queue_item.content}"
                )

                queue_content = json.loads(queue_item.content)
                queue_item_type = queue_content.get("message_type", None)
                match queue_item_type:
                    case global_constants.queue_message_types.keyword_analysis:
                        self.process_keyword_analysis(queue_item=queue_item)

                    case global_constants.queue_message_types.folder_scan:
                        self.process_folder_scan(queue_item=queue_item)

                    case global_constants.queue_message_types.msds_artifact_upload:
                        self.process_artifact_upload(queue_item=queue_item)

                    case _:
                        self.logger.error(
                            f"Thread : {thread_id} :: Invalid message type : {queue_item_type}"
                        )
                        azure_queue_util.delete_queue_item(queue_item)

            # Handle unknown exceptions
            except Exception as e:
                self.logger.exception(
                    f"Thread : {thread_id} :: Error :{str(e)}",
                )
