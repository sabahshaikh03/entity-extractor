import json
from app.modules.keyword_analysis.constants import KeywordAnalysisConstants
from app.modules.keyword_analysis.services.file_analysis_service import (
    FileAnalysisService,
)
from utils.encoding import Encoding
from datetime import datetime

constants = KeywordAnalysisConstants


class HandleQueueItem:
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
