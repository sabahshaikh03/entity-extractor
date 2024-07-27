import re
import os
import time
import json
import asyncio
import urllib.parse
from azure.core.exceptions import ResourceNotFoundError
from azure.ai.vision.imageanalysis.models import VisualFeatures
from connectors.azure_vision_connector import AzureVisionConnector
from connectors.blob_storage_connector import AzureBlobStorageConnector
from connectors.sharepoint_connector import SharePointConnector
from app.modules.keyword_analysis.constants import KeywordAnalysisConstants
from connectors.key_vault_connector import AzureKeyVaultConnector
from utils.azure_blob_storage import BlobStorage
from utils.sharepoint import SharePoint
from global_constants import GlobalConstants
from utils.azure_queue import AzureQueue
from utils.exceptions import MaxProcessingTimeExceededException
from utils.exceptions import FileNotSupportedException
from utils.exceptions import Doc2PDFConversionError
from utils.encoding import Encoding
from azure.core.exceptions import HttpResponseError
import random
import fitz
import io
from PIL import Image
import psutil
from tempfile import NamedTemporaryFile
import subprocess
import magic


constants = KeywordAnalysisConstants
global_constants = GlobalConstants


class FileAnalysisService:
    def __init__(self, logger):
        self.azure_vision_ai_connector = AzureVisionConnector()
        self.azure_vision_ai_client = self.azure_vision_ai_connector.connect()

        self.blob_storage_connector = AzureBlobStorageConnector()
        self.blob_storage_container_client = self.blob_storage_connector.connect()

        self.share_point_connector = SharePointConnector()
        self.sharepoint_client = self.share_point_connector.get_client()

        self.blob_storage_util = BlobStorage(self.blob_storage_container_client, logger)
        self.sharepoint_util = SharePoint(self.sharepoint_client)

        self.asyncio_event_loop = asyncio.new_event_loop()

        self.kv_client = AzureKeyVaultConnector()

        self.container_name = self.kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.blob_storage_container_name
        )

        self.blob_storage_base_uri = self.kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.blob_storage_base_uri
        )

        self.azure_queue_util = AzureQueue()

        self.encoder = Encoding()
        self.logger = logger

    def search_keywords_in_extracted_text(
        self,
        page_no,
        keywords,
        extracted_text_data,
        page_analysis,
    ):
        keywords_matched_on_page = set()
        words_matched_on_page = []
        for search_key in keywords:
            for block in extracted_text_data[
                constants.vision_ai_api_response_parameters.blocks
            ]:
                for line in block[constants.vision_ai_api_response_parameters.lines]:
                    for word in line[constants.vision_ai_api_response_parameters.words]:
                        # Search for pattern
                        search_key_pattern = r"\b{}\b".format(re.escape(search_key))
                        if (
                            re.search(search_key_pattern.lower(), word["text"].lower())
                        ) or (search_key.lower() in word["text"].lower()):

                            # collect matched words in set
                            words_matched_on_page.append(word["text"])
                            # collect matched keywords in set
                            keywords_matched_on_page.add(search_key)

                            confidence = round(word["confidence"] * 100, 2)

                            # This is to handle error which was getting while inserting word.bounding_polygon into json file
                            bounding_polygon_json = [
                                coord
                                for point in word["boundingPolygon"]
                                for coord in [point["x"], point["y"]]
                            ]

                            page_analysis[
                                constants.page_analysis_parameters.matched_keywords
                            ].append(
                                {
                                    constants.page_analysis_parameters.keyword: search_key,
                                    constants.page_analysis_parameters.word: word[
                                        "text"
                                    ],
                                    constants.page_analysis_parameters.confidence: confidence,
                                    constants.page_analysis_parameters.coordinates: bounding_polygon_json,
                                }
                            )

        page_analysis[
            constants.page_analysis_parameters.unique_matched_keywords_count
        ] = len(keywords_matched_on_page)
        page_analysis[constants.page_analysis_parameters.matched_keywords_count] = len(
            words_matched_on_page
        )

    def extract_text_from_image_using_azure_vision_api(
        self, image_byte_array, page_no, file_name, thread_id
    ):
        self.logger.info(
            f"Thread : {thread_id} :: {file_name} : Page No - {page_no} : sent to vision.ai"
        )

        result=None
        start_time=time.time()        
        
        # Define initial parameters
        vision_wait_duration = global_constants.vision_wait_duration
        vision_max_duration = global_constants.queue_visiblity_time
        
        while True:
            try:
                result = self.azure_vision_ai_client._analyze_from_image_data(
                    image_byte_array, visual_features=[VisualFeatures.READ]
                )
                self.logger.info(
                    f"Thread : {thread_id} :: {file_name} : Page No - {page_no} : OCR response received"
                )
                break
            
            except HttpResponseError as ex:
                if ex.status_code == global_constants.api_status_codes.rate_limit_exceeded:
                    self.logger.info(
                        f"Thread : {thread_id} :: {file_name} : Page No - {page_no} : API call limit exceeded. Retrying after {vision_wait_duration} seconds."
                    )
                    if (time.time() - start_time + vision_wait_duration) >= vision_max_duration * 0.8:
                        raise MaxProcessingTimeExceededException("Maximum duration exceeded.")  # Raise exception if maximum duration is exceeded
                        break
                    
                    time.sleep(vision_wait_duration)
                    temp_vision_wait_duration = vision_wait_duration * 2
                    vision_wait_duration = temp_vision_wait_duration * 0.8 + random.random() * (temp_vision_wait_duration * 0.2)  # Calculate new duration with jitter
        return result

    def convert_image_to_byte_array(self, image, page_no, file_name, thread_id):
        image_byte_array = io.BytesIO()
        image.save(image_byte_array, format="PNG")
        image_data = image_byte_array.getvalue()
        image_size_bytes = len(image_data)
        image_size_mb = image_size_bytes / (1024 * 1024)
        image_size_mb_rounded = round(image_size_mb, 2)
        self.logger.info(
            f"Thread : {thread_id} :: {file_name} : Page No - {page_no} : size is {image_size_mb_rounded} MB"
        )
        self.logger.info(
            f"Thread : {thread_id} :: {file_name} : Page No - {page_no} : byte array converted to image"
        )
        return image_data

    def get_keywords_from_global_keywords(self, thread_id):
        try:
            blob_client = self.blob_storage_container_client.get_blob_client(
                f"{constants.keyword_analysis_results_folder}/{constants.file_names.global_keywords}"
            )
            blob_data = blob_client.download_blob()
            blob_data_in_bytes = blob_data.readall()
            keywords_json = json.loads(blob_data_in_bytes)
            id, keywords_arr = keywords_json.popitem()
            return keywords_arr

        except ResourceNotFoundError:
            return []

    def update_progress_status(self, status, file_path, content="", thread_id=-1):
        # Delete previous status files
        for file_name in constants.status_files.values():
            try:
                self.blob_storage_util.delete_file_from_blob_storage(
                    file_path=f"{file_path}/{file_name}", thread_id=thread_id
                )
            except ResourceNotFoundError as e:
                self.logger.exception(
                    f"Thread : {thread_id} :: update_progress_status : {file_path} ResourceNotFoundError -  :: {str(e)}"
                )

        # Store new status file
        self.blob_storage_util.upload_file_to_blob_storage(
            type=constants.file_types.lock,
            file_data=content,
            file_path=f"{file_path}/{constants.status_files[status]}",
        )

    def document_to_pdf(self, doc_path, output_folder):
            subprocess.run(['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', output_folder, doc_path], check=True, timeout=constants.conversion_timeout)

    def get_status_of_file_if_already_processed(self, directory_path):
        status_files = {
            constants.statuses.processing: f"{directory_path}/{constants.file_names.processing_lock}",
            constants.statuses.finished: f"{directory_path}/{constants.file_names.finished_lock}",
            constants.statuses.failed: f"{directory_path}/{constants.file_names.failed_lock}",
            constants.statuses.queued: f"{directory_path}/{constants.file_names.queued_lock}",
        }

        for status, prefix in status_files.items():
            blobs = list(
                self.blob_storage_container_client.list_blobs(name_starts_with=prefix)
            )
            if blobs:
                return status

        return None

    def read_json_from_blob(self, folder_path):
        blob_client = self.blob_storage_container_client.get_blob_client(folder_path)
        blob_data = blob_client.download_blob()
        blob_data_in_bytes = blob_data.readall()

        return json.loads(blob_data_in_bytes)

    def get_no_of_pages_processed_for_file(self, file_path):
        blob_list = self.blob_storage_container_client.walk_blobs(
            name_starts_with=file_path,
            delimiter="/",
        )

        return len(list(blob_list))

    def delete_already_processed_pages_for_file(self, file_path):
        blob_list = self.blob_storage_container_client.list_blobs(
            name_starts_with=file_path
        )
        for blob in blob_list:
            try:
                self.blob_storage_container_client.delete_blob(blob.name)
            except ResourceNotFoundError:
                pass
        return True

    def get_file_path_from_blob_uri(self, parsed_url):
        query = parsed_url.query
        fragment = parsed_url.fragment
        path = parsed_url.path

        file_path = path.split(self.container_name + "/", 1)[1]
        if query:
            file_path += constants.query_separator + query
        if fragment:
            file_path += constants.fragment_separator + fragment

        return file_path

    def get_input_file_from_input_source(self, source, file_uri, file_name, thread_id):
        file_byte_stream = None

        # Read file from SharePoint
        if source == constants.input_file_sources.sharepoint:
            file_byte_stream = self.asyncio_event_loop.run_until_complete(
                self.sharepoint_util.read_file_from_share_point(file_uri)
            )
            self.logger.info(
                f"Thread : {thread_id} :: {file_name} : File received for analysis from SharePoint source : {str(file_uri)}"
            )
        
        # Read file from Blob storage
        elif source == constants.input_file_sources.blob:
            parsed_url = urllib.parse.urlsplit(file_uri)
            host = parsed_url.netloc
            path = parsed_url.path
            path_parts = path.split("/")
            container_name = path_parts[1]
            if (
                host != urllib.parse.urlsplit(self.blob_storage_base_uri).netloc
                or container_name != self.container_name
            ):
                raise ResourceNotFoundError

            file_path = self.get_file_path_from_blob_uri(parsed_url)
            file_byte_stream = self.blob_storage_util.get_file_as_bytes_from_blob_storage(file_path)
            self.logger.info(
                f"Thread : {thread_id} :: {file_name} : File received for analysis from blob source: {str(file_path)}"
            )

        # Detect file type using python-magic
        file_type = magic.from_buffer(file_byte_stream, mime=True)

        if file_type not in global_constants.doc_mime_types and file_type != global_constants.pdf_file_type:
            self.logger.warning(
                f"Thread : {thread_id} :: {file_name} : Unsupported file type received: {file_type}."
            )

            raise FileNotSupportedException("Unsupported file type received")
        
        if file_type in global_constants.doc_mime_types:

            TempPdfComplete = False
            TempDocComplete = False
            try:
                self.logger.info(f"Thread : {thread_id} :: {file_name} : Document file received for analysis")
                # Create a Temporary PDF File
                with NamedTemporaryFile(delete=False, suffix=global_constants.pdf_extension) as temp_pdf_file:
                    # Write Document Bytes to Temporary File
                    with open(temp_pdf_file.name.replace(global_constants.pdf_extension, os.path.splitext(file_name)[1]), 'wb') as temp_doc_file:
                        temp_doc_file.write(file_byte_stream)

                    self.logger.info(f"Thread : {thread_id} :: {file_name} : Document file converting to PDF format")

                    TempDocComplete = True

                    # Convert DOC/DOCX to PDF
                    self.document_to_pdf(temp_doc_file.name, os.path.dirname(temp_pdf_file.name))

                    TempPdfComplete = True

                    self.logger.info(f"Thread : {thread_id} :: {file_name} : Document file converted to PDF format")

                    # Read Converted PDF Bytes
                    with open(temp_pdf_file.name, 'rb') as temp_pdf_file:
                        file_byte_stream = temp_pdf_file.read()

            except subprocess.TimeoutExpired as e:
                # Handle timeout Errors (subprocess.TimeoutExpired)
                raise Doc2PDFConversionError(f"TimeoutExpired")
            
            except subprocess.CalledProcessError as e:
                # Handle Conversion Errors (subprocess.CalledProcessError)
                raise Doc2PDFConversionError("Failed trying to convert using conversion library")

            except Exception as e:
                # Handle Conversion Errors (General)
                raise Doc2PDFConversionError(f"Failed conversion file: {str(e)}")
            
            finally:
                if TempDocComplete:
                    # Delete temporary Document File
                    os.remove(temp_doc_file.name)
                if TempPdfComplete:
                    # Delete temporary PDF File
                    os.remove(temp_pdf_file.name)

        # Open the PDF Document with PyMuPDF
        pdf_document = fitz.open("pdf", file_byte_stream)
        return pdf_document, pdf_document.page_count


    def extract_page_text_dict_from_image_and_upload_image_to_blob(
        self, image, page_image_blob_path, page_no, file_name, thread_id
    ):
        image_byte_array = self.convert_image_to_byte_array(
            image, page_no, file_name, thread_id
        )

        # Upload converted image to blob storage
        image_url = self.blob_storage_util.upload_file_to_blob_storage(
            type=constants.file_types.image,
            file_data=image_byte_array,
            file_path=page_image_blob_path,
        )

        # Extract text from image using azure vision api
        extracted_text_array_from_image = (
            self.extract_text_from_image_using_azure_vision_api(
                image_byte_array, page_no, file_name, thread_id
            )
        )
        page_text_json_words_dict = extracted_text_array_from_image.as_dict()

        return page_text_json_words_dict, image_url

    def get_file_analysis_json_for_zombie_file(self, file_path, pages_count):
        file_analysis_result = self.initialize_file_analysis_result()
        for i in range(1, pages_count):
            page_analysis_json = self.blob_storage_util.get_file_content_from_blob_storage(
                file_path=f"{file_path}/{constants.page_folder_prefix}{'{:03}'.format(i)}/{constants.file_names.page_analysis_json}"
            )
            page_analysis_json = json.loads(page_analysis_json)
            page_no = page_analysis_json[constants.page_analysis_parameters.page_number]
            words_count_matched = page_analysis_json[
                constants.page_analysis_parameters.matched_keywords_count
            ]
            file_analysis_result[
                constants.file_analysis_parameters.pagewise_data
            ].append(
                {
                    constants.page_analysis_parameters.page_number: page_no,
                    constants.page_analysis_parameters.words_count_matched: words_count_matched,
                }
            )
            file_analysis_result[
                constants.file_analysis_parameters.words_count_matched
            ] += words_count_matched
        return file_analysis_result

    def initialize_file_analysis_result(self):
        return {
            constants.file_analysis_parameters.file_uri: None,
            constants.file_analysis_parameters.source: None,
            constants.file_analysis_parameters.number_of_pages: 0,
            constants.file_analysis_parameters.words_count_matched: 0,
            constants.file_analysis_parameters.duration_ms: 0,
            constants.file_analysis_parameters.pagewise_data: [],
        }

    def initialize_page_analysis_result(self):
        return {
            constants.page_analysis_parameters.page_number: None,
            constants.page_analysis_parameters.page_image: None,
            constants.page_analysis_parameters.duration_ms: 0,
            constants.page_analysis_parameters.matched_keywords_count: 0,
            constants.page_analysis_parameters.unique_matched_keywords_count: 0,
            constants.page_analysis_parameters.matched_keywords: [],
        }

    def handle_file_status_and_force_flag(
        self,
        file_status,
        blob_storage_output_folder_path_file_level,
        force,
        thread_id,
    ):
        process_file_with_already_extracted_text = False
        start_processing_from_page_no = 1
        file_analysis_result = self.initialize_file_analysis_result()

        if file_status == constants.statuses.processing:
            # If the file is in processing state already it means the process is not finished in one go
            start_processing_from_page_no = self.get_no_of_pages_processed_for_file(
                f"{blob_storage_output_folder_path_file_level}/{constants.page_folder_prefix}"
            )
            file_analysis_result = self.get_file_analysis_json_for_zombie_file(
                blob_storage_output_folder_path_file_level,
                pages_count=start_processing_from_page_no,
            )

        elif force:
            self.delete_already_processed_pages_for_file(
                blob_storage_output_folder_path_file_level
            )
        elif file_status == constants.statuses.finished:
            process_file_with_already_extracted_text = True
        elif file_status == constants.statuses.failed:
            start_processing_from_page_no = self.get_no_of_pages_processed_for_file(
                f"{blob_storage_output_folder_path_file_level}/{constants.page_folder_prefix}"
            )

        return (
            process_file_with_already_extracted_text,
            start_processing_from_page_no,
            file_analysis_result,
        )

    def get_words_to_search(
        self,
        search_scope,
        local_keywords,
        blob_storage_output_folder_path_file_level,
        thread_id,
    ):
        words_to_search = []
        if search_scope == constants.search_scopes.local_scope:
            words_to_search = local_keywords
        elif search_scope == constants.search_scopes.global_scope:
            words_to_search = self.get_keywords_from_global_keywords(thread_id)
        elif search_scope == constants.search_scopes.both:
            words_to_search = local_keywords
            words_to_search.extend(self.get_keywords_from_global_keywords(thread_id))

        keywords_dict = {constants.keywords: words_to_search}
        keywords_json_url = self.blob_storage_util.upload_file_to_blob_storage(
            type=constants.file_types.json,
            file_data=keywords_dict,
            file_path=f"{blob_storage_output_folder_path_file_level}/{constants.file_names.keywords}",
        )
        return words_to_search

    def get_page_text_json(
        self,
        process_file_with_already_extracted_text,
        page_image_blob_path,
        page_text_array_blob_path,
        page_no,
        page_analysis,
        file_name,
        thread_id,
        image=None,
    ):
        image_url = None
        page_text_json = None
        if process_file_with_already_extracted_text:
            image_url = self.blob_storage_util.get_uri_from_path(page_image_blob_path)
            page_text_json = self.read_json_from_blob(page_text_array_blob_path)
        else:
            # Get page text dict from image and upload image to blob storage
            page_text_json, image_url = (
                self.extract_page_text_dict_from_image_and_upload_image_to_blob(
                    image=image,
                    page_image_blob_path=page_image_blob_path,
                    page_no=page_no,
                    file_name=file_name,
                    thread_id=thread_id,
                )
            )

            # Save extracted text output in text file and store it in blob storage
            self.blob_storage_util.upload_file_to_blob_storage(
                type=constants.file_types.json,
                file_data=page_text_json,
                file_path=page_text_array_blob_path,
            )

        page_text_json = page_text_json[
            constants.vision_ai_api_response_parameters.read_result
        ]
        page_analysis[constants.page_analysis_parameters.page_number] = page_no
        page_analysis[constants.page_analysis_parameters.page_image] = image_url
        return page_text_json

    def process_memory(self):
        process = psutil.Process(os.getpid())
        mem_used_mb = round(
            process.memory_info().rss / (1024 * 1024), 2
        )  # Convert to MB

        # Get total memory and available memory
        mem_info = psutil.virtual_memory()
        total_memory_mb = round(mem_info.total / (1024 * 1024), 2)  # Convert to MB
        available_memory_mb = round(
            mem_info.available / (1024 * 1024), 2
        )  # Convert to MB

        # Format the result as a string
        return f"{mem_used_mb }/{total_memory_mb}"
    
    def system_cpu(self):
         # Get system-wide CPU usage
        system_cpu_percent = psutil.cpu_percent(interval=0.2)

         # Format the result as a string
        return f"{system_cpu_percent}%"

    def concat_json_dict_data_into_string(self, json_dict):
        # Concat all the text data from page text dict
        blocks = json_dict[constants.vision_ai_api_response_parameters.blocks]
        page_text_data = " ".join(
            line[constants.vision_ai_api_response_parameters.text]
            for block in blocks
            for line in block[constants.vision_ai_api_response_parameters.lines]
        )
        return page_text_data

    def pdf_doc_to_image(self, pdf_document, page_num):
        """
        Convert a PDF file in bytes to a list of images.

        Parameters:
        pdf_bytes (bytes): PDF file in bytes.

        Returns:
        list: A list of PIL Image objects representing each page of the PDF.
        """

        # Render the page to a pixmap (image)
        pix = pdf_document.load_page(page_num).get_pixmap(dpi=200)

        # Convert pixmap to an image using Pillow
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        return img

    def get_file_name_from_file_uri(self, file_uri, input_file_source):
        file_name = ""
        if input_file_source == constants.input_file_sources.blob:
            # Get input file name from blob uri
            file_name = self.blob_storage_util.get_file_name_from_blob_uri(file_uri)
        return file_name

    def process_page(
        self,
        page_no,
        pdf_document,
        file_name,
        blob_storage_output_folder_path_file_level,
        process_file_with_already_extracted_text,
        words_to_search,
        thread_id,
    ):
        # Initialing variables
        page_processing_start_time = time.time()
        blob_storage_output_folder_path_page_level = f"{blob_storage_output_folder_path_file_level}/{constants.page_folder_prefix}{'{:03}'.format(page_no)}"
        page_text_array_blob_path = f"{blob_storage_output_folder_path_page_level}/{constants.file_names.page_text_json}"
        page_image_blob_path = f"{blob_storage_output_folder_path_page_level}/{constants.file_names.page_image}"

        # Initialize empty page analysis result json
        page_analysis = self.initialize_page_analysis_result()

        # Get page_text json from blob if already extracted or generate from image
        image = (
            None
            if process_file_with_already_extracted_text
            else self.pdf_doc_to_image(pdf_document, page_no - 1)
        )

        page_text_json = self.get_page_text_json(
            process_file_with_already_extracted_text,
            page_image_blob_path,
            page_text_array_blob_path,
            page_no,
            page_analysis,
            file_name,
            thread_id,
            image,
        )

        # Concat all the text data from page text dict
        page_text_data = self.concat_json_dict_data_into_string(page_text_json)

        # Upload extracted text data to blob storage
        self.blob_storage_util.upload_file_to_blob_storage(
            type=constants.file_types.txt,
            file_data=page_text_data,
            file_path=f"{blob_storage_output_folder_path_page_level}/{constants.file_names.page_text}",
        )

        # Logging
        self.logger.info(
            f"Thread : {thread_id} :: {file_name} : Page No - {page_no} : Keywords analysis started"
        )

        # Search keywords in extracted text data
        self.search_keywords_in_extracted_text(
            page_no,
            words_to_search,
            page_text_json,
            page_analysis,
        )

        duration_ms = (time.time() - page_processing_start_time) * 1000

        # Logging
        self.logger.info(
            f"Thread : {thread_id} :: {file_name} : Page No - {page_no} : Keywords analysis finished :: {duration_ms} milliseconds",
        )

        # Update page analysis and file analysis json with page processing details
        page_analysis[constants.page_analysis_parameters.duration_ms] = duration_ms
        page_analysis[constants.page_analysis_parameters.matched_keywords_count] = (
            page_analysis[constants.page_analysis_parameters.matched_keywords_count]
        )

        # Upload pagewise analysis json to blob storage
        self.blob_storage_util.upload_file_to_blob_storage(
            type=constants.file_types.json,
            file_data=page_analysis,
            file_path=f"{blob_storage_output_folder_path_page_level}/{constants.file_names.page_analysis_json}",
        )

        return page_analysis

    def process_queue_item(
        self,
        queue_item,
        file_uri,
        input_file_source,
        search_scope,
        local_keywords,
        force,
        thread_id,
    ):
        try:
            start_Time = time.time()
            max_processing_time = int(global_constants.queue_visiblity_time * 0.9)

            # Encode input file uri using base64 encoding
            base64_encoded_file_uri = self.encoder.encode_data(file_uri)

            # Create output folder path for blob storage
            blob_storage_output_folder_path_file_level = (
                f"{constants.output_folder_name}/{base64_encoded_file_uri}"
            )

            # Get input file name from file uri
            file_name = self.get_file_name_from_file_uri(file_uri, input_file_source)

            self.logger.info(
                f"[Memory: {self.process_memory()}, CPU: {self.system_cpu()}] Thread : {thread_id} :: {file_name} : {base64_encoded_file_uri} : Processing started",
            )

            # Get status of file if already processed
            file_status = self.get_status_of_file_if_already_processed(
                blob_storage_output_folder_path_file_level
            )

            # Handle file status if already processed and force flag
            (
                process_file_with_already_extracted_text,
                start_processing_from_page_no,
                file_analysis_result,
            ) = self.handle_file_status_and_force_flag(
                file_status,
                blob_storage_output_folder_path_file_level,
                force,
                thread_id,
            )

            # Logging
            self.logger.info(
                f"Thread : {thread_id} :: {file_name} : File analysis process started for {base64_encoded_file_uri}",
            )
            file_processing_start_time = time.time()

            # Upload processing.lock file to blob storage to indicate file is in progress
            self.update_progress_status(
                status=constants.statuses.processing,
                file_path=blob_storage_output_folder_path_file_level,
                thread_id=thread_id,
            )

            # Get keywords from blob storage based on search scope and upload keywords to blob storage
            words_to_search = self.get_words_to_search(
                search_scope,
                local_keywords,
                blob_storage_output_folder_path_file_level,
                thread_id,
            )

            # Get total no of pages in file and pdf document object
            pdf_document, total_no_of_pages_in_file = None, 0
            if process_file_with_already_extracted_text:
                # file is always going to be status false so counting no of pages processed already
                total_no_of_pages_in_file = self.get_no_of_pages_processed_for_file(
                    f"{blob_storage_output_folder_path_file_level}/{constants.page_folder_prefix}"
                )
            else:
                pdf_document, total_no_of_pages_in_file = (
                    self.get_input_file_from_input_source(
                        source=input_file_source,
                        file_uri=file_uri,
                        file_name=file_name,
                        thread_id=thread_id,
                    )
                )
            self.logger.info(
                f"Thread : {thread_id} :: {file_name} : Page analysis process started for {base64_encoded_file_uri}",
            )
            for i in range(
                start_processing_from_page_no - 1, total_no_of_pages_in_file
            ):
                page_no = i + 1
                # Process pdf page and get page analysis json
                page_analysis = self.process_page(
                    page_no,
                    pdf_document,
                    file_name,
                    blob_storage_output_folder_path_file_level,
                    process_file_with_already_extracted_text,
                    words_to_search,
                    thread_id,
                )

                # Update file analysis json with page processing details
                words_count_matched = page_analysis[
                    constants.page_analysis_parameters.matched_keywords_count
                ]
                file_analysis_result[
                    constants.file_analysis_parameters.words_count_matched
                ] += words_count_matched
                file_analysis_result[
                    constants.file_analysis_parameters.pagewise_data
                ].append(
                    {
                        constants.page_analysis_parameters.page_number: page_no,
                        constants.page_analysis_parameters.words_count_matched: words_count_matched,
                    }
                )

                # If the processing time exceeds max processing time then raise exception
                if time.time() - start_Time > max_processing_time:
                    visibility_timeout = (time.time() - start_Time) + int(
                        global_constants.queue_visiblity_time
                    )
                    self.logger.info(
                        f"Thread : {thread_id} :: {file_name} : visibility timeout is {visibility_timeout} seconds for {base64_encoded_file_uri}",
                    )
                    updated_message = self.azure_queue_util.update_queue_message(
                        message_id=queue_item.id,
                        pop_receipt=queue_item.pop_receipt,
                        visibility_timeout=visibility_timeout,
                    )
                    queue_item = updated_message
                    max_processing_time = visibility_timeout * 0.9

                    self.logger.warn(
                        f"Thread : {thread_id} :: {file_name} : Max processing time reached for file {base64_encoded_file_uri} - increasing visibility timeout to {max_processing_time}.",
                    )
            self.logger.info(
                f"Thread : {thread_id} :: {file_name} : Page analysis process completed for {base64_encoded_file_uri}",
            )
            
            # Update file analysis json with file processing details
            duration_ms = (time.time() - file_processing_start_time) * 1000
            file_analysis_result.update(
                {
                    constants.file_analysis_parameters.file_uri: file_uri,
                    constants.file_analysis_parameters.source: input_file_source,
                    constants.file_analysis_parameters.number_of_pages: total_no_of_pages_in_file,
                    constants.file_analysis_parameters.duration_ms: duration_ms,
                }
            )

            # Store json data to blob storage
            self.blob_storage_util.upload_file_to_blob_storage(
                type=constants.file_types.json,
                file_data=file_analysis_result,
                file_path=f"{blob_storage_output_folder_path_file_level}/{constants.file_names.file_analysis_json}",
            )

            # Upload finished.lock file with count of pages to blob storage to indicate file processing finished
            self.update_progress_status(
                status=constants.statuses.finished,
                file_path=blob_storage_output_folder_path_file_level,
                content=str(total_no_of_pages_in_file),
                thread_id=thread_id,
            )

            # Logging
            self.logger.info(
                f"Thread : {thread_id} :: File Name: {file_name}, Status: File analysis process completed Total Pages: {total_no_of_pages_in_file}, Base64 Encoded File URI: {base64_encoded_file_uri}, File URI: {file_uri}, Total Duration: {duration_ms} milliseconds."
            )

            

        except MaxProcessingTimeExceededException as e:
            """
            This exception is handled in parent function (run.py)
            This file will be processed by different thread later as it took 90% of queue visibility time
            So raising this exception back to thread function so that this queue item wont be deleted.
            """
            self.logger.warning(
                f"Thread : {thread_id} :: {file_name} : Max processing time reached for file: {base64_encoded_file_uri}"
            )
            raise

        except FileNotSupportedException as e:
            self.logger.exception(
                f"Thread : {thread_id} :: {file_name} : FileNotSupported - {base64_encoded_file_uri} :: {str(e)}"
            )
            self.update_progress_status(
                status=constants.statuses.failed,
                file_path=blob_storage_output_folder_path_file_level,
                content=constants.messages.unsupported_file_type,
                thread_id=thread_id,
            )
        
        except Doc2PDFConversionError as e:
            self.logger.exception(
                f"Thread : {thread_id} :: {file_name} : Document to PDF conversion error - {base64_encoded_file_uri} :: {str(e)}"
            )
            self.update_progress_status(
                status=constants.statuses.failed,
                file_path=blob_storage_output_folder_path_file_level,
                content=constants.messages.conversion_error,
                thread_id=thread_id,
            )
        except ResourceNotFoundError as e:
            self.logger.exception(
                f"Thread : {thread_id} :: {file_name} : ResourceNotFoundError - {base64_encoded_file_uri} :: {str(e)}"
            )
            self.update_progress_status(
                status=constants.statuses.failed,
                file_path=blob_storage_output_folder_path_file_level,
                content=constants.messages.blob_not_found,
                thread_id=thread_id,
            )

        except Exception as e:
            self.logger.exception(
                f"Thread : {thread_id} :: {file_name} : Error while processing file - {base64_encoded_file_uri} :: {str(e)}"
            )
            # Upload failed.lock file with error to blob storage to indicate file processing finished
            self.update_progress_status(
                status=constants.statuses.failed,
                file_path=blob_storage_output_folder_path_file_level,
                content=str(e),
                thread_id=thread_id,
            )
        return queue_item
    def enqueue_api_request(
        self, file_uri, search_scope, input_file_source, local_keywords, force
    ):

        # Encode input file uri using base64 encoding
        base64_encoded_file_uri = self.encoder.encode_data(file_uri)

        # Create output folder path for blob storage
        blob_storage_output_folder_path_file_level = (
            f"{constants.output_folder_name}/{base64_encoded_file_uri}"
        )

        # Get status of file if already processed
        file_status = self.get_status_of_file_if_already_processed(
            blob_storage_output_folder_path_file_level
        )

        # Return response if file is already processing irrespective of force flag
        if file_status == constants.statuses.processing:
            return {
                global_constants.api_response_parameters.status: global_constants.api_status_codes.bad_request,
                global_constants.api_response_parameters.message: constants.messages.file_is_in_processing,
            }

        # Add api payload to azure queue
        args = {
            constants.api_parameters.file_uri: file_uri,
            constants.api_parameters.source: input_file_source,
            constants.api_parameters.search_scope: search_scope,
            constants.api_parameters.keywords: local_keywords,
            constants.api_parameters.force: force,
        }

        # Upload queued.lock file to indicate file is queued for processing
        self.update_progress_status(
            status=constants.statuses.queued,
            file_path=blob_storage_output_folder_path_file_level,
        )

        try:
            self.azure_queue_util.enqueue(args)
        except Exception as e:
            # Upload failed.lock file to indicate that enqueue failed
            self.update_progress_status(
                status=constants.statuses.failed,
                file_path=blob_storage_output_folder_path_file_level,
                content=str(e),
            )

        return {
            global_constants.api_response_parameters.status: global_constants.api_status_codes.ok,
            global_constants.api_response_parameters.message: global_constants.api_response_messages.accepted,
            global_constants.api_response_parameters.identifier: base64_encoded_file_uri,
        }

    def get_status_of_file(self, file_url_base64_encoded):
        base_dir = f"{constants.output_folder_name}/{file_url_base64_encoded}"
        processing_lock_path = f"{base_dir}/{constants.file_names.processing_lock}"
        finished_lock_path = f"{base_dir}/{constants.file_names.finished_lock}"
        failed_lock_path = f"{base_dir}/{constants.file_names.failed_lock}"
        queued_lock_path = f"{base_dir}/{constants.file_names.queued_lock}"

        if self.blob_storage_util.check_if_directory_exists(base_dir):

            if self.blob_storage_util.check_if_directory_exists(
                queued_lock_path
            ) or self.blob_storage_util.check_if_directory_exists(processing_lock_path):
                return constants.statuses.processing, None

            elif self.blob_storage_util.check_if_directory_exists(finished_lock_path):
                no_of_pages = (
                    self.blob_storage_util.get_file_content_as_text_from_blob_storage(
                        finished_lock_path
                    )
                )

                return constants.statuses.success, {
                    constants.api_parameters.total_pages: int(no_of_pages),
                    constants.api_parameters.file_uri: f"{self.blob_storage_base_uri}/{base_dir}",
                }
            elif self.blob_storage_util.check_if_directory_exists(failed_lock_path):
                error_message = (
                    self.blob_storage_util.get_file_content_as_text_from_blob_storage(
                        failed_lock_path
                    )
                )
                return constants.statuses.failed, {
                    global_constants.api_response_parameters.reason: f"{global_constants.api_response_messages.error_while_processing_file} : {error_message}"
                }

        return constants.statuses.failed, constants.messages.invalid_file_identifier
