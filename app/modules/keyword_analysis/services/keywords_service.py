import json
from connectors.blob_storage_connector import AzureBlobStorageConnector
from azure.core.exceptions import ResourceNotFoundError
from app.modules.keyword_analysis.constants import KeywordAnalysisConstants


class KeywordsService:
    def __init__(self, logger, global_constants):
        self.logger = logger
        self.global_constants = global_constants
        self.constants = KeywordAnalysisConstants
        self.blob_storage_connector = AzureBlobStorageConnector(self.global_constants)
        self.blob_storage_container_client = self.blob_storage_connector.connect()

    def get_keyword_from_blob_storage(self, file_path):
        try:
            blob_client = self.blob_storage_container_client.get_blob_client(file_path)
            blob_data = blob_client.download_blob()
            blob_data_in_bytes = blob_data.readall()
            keywords_json = json.loads(blob_data_in_bytes)
            return keywords_json
        except ResourceNotFoundError:
            return {}

    def store_keywords_in_blob_storage(self, keywords_json, file_path):
        blob_client = self.blob_storage_container_client.get_blob_client(file_path)
        keywords_json_data = json.dumps(keywords_json).encode(self.constants.utf_8)
        blob_client.upload_blob(
            keywords_json_data,
            blob_type=self.constants.blob_types.block_blob,
            overwrite=True,
        )
        return blob_client.url

    def get_keywords_id(self):
        file_path = f"{self.constants.keyword_analysis_results_folder}/{self.constants.file_names.global_keywords}"
        keywords_json = self.get_keyword_from_blob_storage(file_path)
        keyword_id_list = list(keywords_json.keys())
        if len(keyword_id_list) == 1:
            return keyword_id_list[0]
        else:
            return None

    def store_keywords(self, id, keywords):
        file_path = f"{self.constants.keyword_analysis_results_folder}/{self.constants.file_names.global_keywords}"
        keywords_json = {id: keywords}
        self.store_keywords_in_blob_storage(keywords_json, file_path)
