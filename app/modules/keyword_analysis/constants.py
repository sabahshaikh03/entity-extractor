import os
from utils.dot_access_dict import DotAccessDict


class KeywordAnalysisConstants:
    utf_8 = "utf-8"
    output_folder_name = "keyword_analysis_results/documents"
    keyword_analysis_results_folder = "keyword_analysis_results"
    keywords = "keywords"
    valid_search_scopes = ["local", "global", "both", None]
    valid_force_parameters = [False, True, None]
    fragment_separator = "#"
    query_separator = "?"
    conversion_timeout = int(os.getenv("ConversionTimeout", 600))
    max_pix_width = 10000
    max_pix_height = 10000
    min_pix_width = 50
    min_pix_height = 50

    page_folder_prefix = "page_"

    messages = {
        "processing": "Processing",
        "success": "Success",
        "failed": "Failed",
        "invalid_file_identifier": "Invalid file identifier",
        "file_already_processed": "File already processed",
        "file_is_in_processing": "File is in processing",
        "file_uri_is_not_valid": "File uri is not valid",
        "rate_limit_exceeded": "API rate limit exceeded",
        "blob_not_found": "Blob not found",
        "unsupported_file_type": "Unsupported file type received",
        "conversion_error": "Document to PDF conversion error",
    }

    messages = DotAccessDict(messages)

    file_analysis_parameters = {
        "file_uri": "file_uri",
        "number_of_pages": "number_of_pages",
        "words_count_matched": "words_count_matched",
        "pagewise_data": "pagewise_data",
        "source": "source",
        "duration_ms": "duration_ms",
    }

    file_analysis_parameters = DotAccessDict(file_analysis_parameters)

    page_analysis_parameters = {
        "matched_keywords": "matched_keywords",
        "matched_keywords_count": "matched_keywords_count",
        "word": "word",
        "keyword": "keyword",
        "confidence": "confidence",
        "coordinates": "coordinates",
        "page_number": "page_number",
        "page_image": "page_image",
        "duration_ms": "duration_ms",
        "words_count_matched": "words_count_matched",
        "page_words_matched_count": "page_words_matched_count",
        "unique_matched_keywords_count": "unique_matched_keywords_count",
    }
    page_analysis_parameters = DotAccessDict(page_analysis_parameters)

    vision_ai_api_response_parameters = {
        "read_result": "readResult",
        "blocks": "blocks",
        "lines": "lines",
        "words": "words",
        "text": "text",
    }
    vision_ai_api_response_parameters = DotAccessDict(vision_ai_api_response_parameters)

    search_scopes = {
        "global_scope": "global",
        "local_scope": "local",
        "both": "both",
        "default": "both",
    }

    search_scopes = DotAccessDict(search_scopes)

    api_parameters = {
        "keywords": "keywords",
        "force": "force",
        "id": "id",
        "file_uri": "file_uri",
        "search_scope": "search_scope",
        "file_identifier": "file_identifier",
        "source": "source",
        "total_pages": "total_pages",
        "file_status_if_previously_processed": "file_status_if_previously_processed",
    }
    api_parameters = DotAccessDict(api_parameters)

    file_types = {
        "txt": "txt",
        "pdf": "pdf",
        "image": "image",
        "jpg": "jpg",
        "png": "png",
        "json": "json",
        "lock": "lock",
    }
    file_types = DotAccessDict(file_types)

    input_file_sources = {"blob": "blob", "sharepoint": "sharepoint"}
    input_file_sources = DotAccessDict(input_file_sources)

    file_names = {
        "processing_lock": "processing.lock",
        "finished_lock": "finished.lock",
        "failed_lock": "failed.lock",
        "queued_lock": "queued.lock",
        "keywords": "keywords.json",
        "global_keywords": "global_keywords.json",
        "page_analysis_json": "analysis.json",
        "page_text": "page_text.txt",
        "file_analysis_json": "file_analysis.json",
        "page_image": "image.png",
        "page_text_json": "text.json",
    }

    file_names = DotAccessDict(file_names)

    statuses = {
        "processing": "processing",
        "finished": "finished",
        "failed": "failed",
        "success": "success",
        "queued": "queued",
    }
    statuses = DotAccessDict(statuses)

    status_files = {
        "processing": "processing.lock",
        "finished": "finished.lock",
        "failed": "failed.lock",
        "queued": "queued.lock",
    }
    status_files = DotAccessDict(status_files)

    blob_types = {
        "block_blob": "BlockBlob",
    }

    blob_types = DotAccessDict(blob_types)
