import json
from global_constants import GlobalConstants
from app.modules.keyword_analysis.constants import KeywordAnalysisConstants
from urllib.parse import urlparse
from logging import Logger
from azure.storage.blob import BlobServiceClient


constants = KeywordAnalysisConstants
globa_constants = GlobalConstants


class BlobStorage:
    def __init__(self, blob_storage_client: BlobServiceClient, logger: Logger):
        self.blob_storage_container_client = blob_storage_client
        self.logger = logger

    def upload_file_to_blob_storage(self, type, file_data, file_path):
        blob_client = self.blob_storage_container_client.get_blob_client(file_path)

        if type == globa_constants.file_types.json:
            json_data = json.dumps(file_data)
            file_data = json_data.encode(globa_constants.utf_8)

        blob_client.upload_blob(
            file_data, blob_type=globa_constants.blob_types.block_blob, overwrite=True
        )
        return blob_client.url

    def delete_file_from_blob_storage(self, file_path, thread_id=-1):
        blob_client = self.blob_storage_container_client.get_blob_client(file_path)
        if blob_client.exists():
            blob_client.delete_blob()
            return True
        else:
            return False

    def check_if_directory_exists(self, path):
        blob_list = self.blob_storage_container_client.list_blobs(name_starts_with=path)
        blob_list = list(blob_list)
        if len(blob_list) > 0:
            return True
        else:
            return False

    def get_no_of_files_in_folder(self, path):
        blob_list = self.blob_storage_container_client.list_blobs(prefix=path)
        return len(list(blob_list))

    def get_file_content_as_text_from_blob_storage(self, file_path):
        blob_client = self.blob_storage_container_client.get_blob_client(file_path)
        file = blob_client.download_blob()
        return file.content_as_text()

    def get_file_content_from_blob_storage(self, file_path):
        blob_client = self.blob_storage_container_client.get_blob_client(file_path)
        file = blob_client.download_blob()
        return file.readall()

    def get_file_as_bytes_from_blob_storage(self, file_path):
        blob_client = self.blob_storage_container_client.get_blob_client(file_path)
        file = blob_client.download_blob()
        return file.content_as_bytes()

    def get_uri_from_path(self, path):
        blob_client = self.blob_storage_container_client.get_blob_client(path)
        return blob_client.url

    def get_file_name_from_blob_uri(self, file_uri):
        parsed_uri = urlparse(file_uri)
        file_name = parsed_uri.path.split("/")[-1]
        fragment = parsed_uri.fragment
        query = parsed_uri.query
        if query:
            file_name += constants.query_separator + query
        if fragment:
            file_name += constants.fragment_separator + fragment

        return file_name

    def get_file_properties(self, file_path):
        blob_client = self.blob_storage_container_client.get_blob_client(file_path)
        blob_properties = blob_client.get_blob_properties()
        return blob_properties
