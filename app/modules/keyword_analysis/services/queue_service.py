import json
from connectors.key_vault_connector import AzureKeyVaultConnector
from global_constants import GlobalConstants
from utils.threading_tools import ThreadingTool
from utils.azure_queue import AzureQueue
from app.modules.keyword_analysis.constants import KeywordAnalysisConstants
from utils.exceptions import MaxProcessingTimeExceededException
from app.modules.keyword_analysis.services.file_analysis_service import (
    FileAnalysisService,
)
from utils.encoding import Encoding
from datetime import datetime
import time

constants = KeywordAnalysisConstants
global_constants = GlobalConstants
kv_client = AzureKeyVaultConnector()
threading_tool = ThreadingTool
azure_queue_util = AzureQueue()


class QueueService:
    def __init__(self, logger):
        self.logger = logger
        self.file_analysis_service = FileAnalysisService(logger)
        self.encoder = Encoding()
        
    def extract_api_parameters_and_process_queue_item(self, queue_item, thread_id):
        try:
            # Logging
            start_time = datetime.now().strftime("%H:%M:%S")
            self.logger.info(f"Thread : {thread_id} :: Start time : {start_time}")

            # Get queue content and convert it to json
            request_data = json.loads(queue_item.content)

            # Extract api payload parameters from queue item
            file_uri = request_data.get(constants.api_parameters.file_uri)
            source = request_data.get(constants.api_parameters.source)
            force = request_data.get(constants.api_parameters.force, False)
            keywords_to_search = request_data.get(constants.api_parameters.keywords, [])
            search_scope = request_data.get(
                constants.api_parameters.search_scope,
                constants.search_scopes.default,
            )
            # Call keyword analysis function for queue item
            processed_queue_item = self.file_analysis_service.process_queue_item(
                queue_item=queue_item,
                file_uri=file_uri,
                input_file_source=source,
                search_scope=search_scope,
                local_keywords=keywords_to_search,
                force=force,
                thread_id=thread_id,
            )
            return file_uri, processed_queue_item
        
        # If the queue item is not json serielized it will throw an error
        except json.decoder.JSONDecodeError:
            self.logger.exception(f"Thread : {thread_id} :: Error while decoding json")

    def process_waiting_api_calls(self, thread_id):
        self.logger.info(f"Thread : {thread_id} :: Started...")
        while True:
            try:
                # Get queue item from azure queue
                queue_item = azure_queue_util.dequeue(
                    visiblity_timeout=global_constants.queue_visiblity_time
                )

                if queue_item:
                    self.logger.info(f"Thread : {thread_id} :: Items in queue : {azure_queue_util.get_queue_length()}.")
                    # Extract api parameters from queue item and process it
                    file_uri, processed_queue_item = self.extract_api_parameters_and_process_queue_item(
                        queue_item, thread_id
                    )
                    if file_uri and processed_queue_item:
                        base64_encoded_file_uri = self.encoder.encode_data(file_uri)
                        # Delete queue item after processing
                        azure_queue_util.delete_queue_item(processed_queue_item)
                        self.logger.info(
                            f"Thread : {thread_id} :: Queue item deleted for {base64_encoded_file_uri} [{file_uri}]"
                        )
                else:
                    time.sleep(5)

            # If max processing time is reached, the file will processed later
            except MaxProcessingTimeExceededException:
                pass

            # Handle unknown exceptions
            except Exception as e:
                self.logger.exception(
                    f"Thread : {thread_id} :: Error :{str(e)}",
                )
