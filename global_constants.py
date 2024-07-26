import os


class DotAccessDict(dict):
    def __getattr__(self, attr):
        if attr in self:
            return self[attr]
        else:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{attr}'"
            )


class GlobalConstants(DotAccessDict):
    api_version = "/v1"
    utf_8 = "utf-8"
    graph_service_scope = "https://graph.microsoft.com/.default"
    flask_app_port = os.getenv("WEBSITES_PORT", 8000)
    flask_host = "0.0.0.0"
    u = "u"
    queue_visiblity_time = int(os.getenv("QueueVisiblityTime", 300))
    azure_kv_uri = os.getenv("AZURE_KEY_VAULT_URL", None)
    no_of_threads = int(os.getenv("NoOfThreads", 20))
    azure_client_id = "AZURE_CLIENT_ID"
    azure_client_secret = "AZURE_CLIENT_SECRET"
    azure_tenant_id = "AZURE_TENANT_ID"
    swagger_json_api_endpoint = "/v1/api/swagger.json"
    swagger_app_name = "Keyword Analysis API"
    swagger_endpoint = os.getenv("SwaggerEndpoint", "/api/docs")
    vision_wait_duration = int(os.getenv("VisionWaitDuration", 5))
    doc_mime_types = [
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-word.document.macroEnabled.12",
        "application/vnd.ms-word.template.macroEnabled.12",
        "application/vnd.ms-word.template",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
    ]
    pdf_extension = ".pdf"
    pdf_file_type = "application/pdf"
    enabled_flag = "true"
    disabled_flag = "false"

    swagger_config = {
        "app_name": "Keyword Analysis API",  # Set the title of your API
        "docExpansion": "none",  # Controls the default expansion setting for the operations and tags
        "displayOperationId": True,  # Controls the display of operation Ids in operations list
        "displayRequestDuration": True,  # Controls the display of the request duration in the response
        "defaultModelsExpandDepth": 0,  # The default expansion depth for the model on the model-example section
        "defaultModelExpandDepth": 1,  # The default expansion depth for the model on the model section
    }

    basic_auth_parameters = {
        "basic_auth_username": "BasicAuthUsername",
        "basic_auth_realm": "BasicAuthRealm",
        "basic_auth_password": "BasicAuthPassword",
        "www_authenticate": "WWW-Authenticate",
    }
    basic_auth_parameters = DotAccessDict(basic_auth_parameters)

    auth_types = {
        "basic": "basic",
    }
    auth_types = DotAccessDict(auth_types)

    api_response_parameters = {
        "status": "status",
        "message": "message",
        "result": "result",
        "identifier": "identifier",
        "id": "id",
        "status_code": "status_code",
        "missing_parameters": "Missing parameters",
        "reason": "reason",
    }

    api_response_parameters = DotAccessDict(api_response_parameters)

    apispec_config = {
        "title": "Keyword Analysis API",
        "version": "1.0.0",
        "openapi_version": "3.0.2",
    }

    apispec_config = DotAccessDict(apispec_config)

    symbols = {
        "plus": "+",
        "minus": "-",
        "star": "*",
        "equal_to": "=",
        "forward_slash": "/",
        "underscore": "_",
        "empty_string": "",
        "exclamatory_mark": "!",
    }

    symbols = DotAccessDict(symbols)

    rest_api_methods = {
        "post": "POST",
        "get_api": "GET",  # Using "get_api" because "get" is reserved keyword
        "put": "PUT",
        "delete": "DELETE",
        "patch": "PATCH",
    }

    rest_api_methods = DotAccessDict(rest_api_methods)

    api_status_codes = {
        "ok": 200,
        "created": 201,
        "no_content": 204,
        "bad_request": 400,
        "unauthorized": 401,
        "forbidden": 403,
        "not_found": 404,
        "method_not_allowed": 405,
        "conflict": 409,
        "internal_server_error": 500,
        "service_unavailable": 503,
        "rate_limit_exceeded": 429,
    }
    api_status_codes = DotAccessDict(api_status_codes)

    api_response_messages = {
        "success": "Success",
        "accepted": "Accepted",
        "invalid_request_data": "Invalid request data",
        "unauthorized": "Unauthorized access",
        "forbidden": "Forbidden access",
        "not_found": "Resource not found",
        "global_keywords_not_configured": "Global keywords not configured",
        "method_not_allowed": "Method not allowed for the requested resource",
        "conflict": "Conflict with current state of the resource",
        "internal_server_error": "Internal server error occurred",
        "service_unavailable": "Service temporarily unavailable",
        "server_is_running": "Keyword Analysis App Service is running",
        "missing_required_parameters": "Missing required parameters",
        "error_while_processing_file": "Error while processing file",
    }

    api_response_messages = DotAccessDict(api_response_messages)

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

    queue_message_types = {
        "keyword_analysis": "keyword-analysis",
        "folder_scan": "folder-scan",
        "msds_artifact_upload": "msds-artifact-upload",
    }

    queue_message_types = DotAccessDict(queue_message_types)

    file_extensions = {
        "txt": "txt",
        "pdf": "pdf",
        "image": "img",
        "jpg": "jpg",
        "png": "png",
        "json": "json",
        "lock": "lock",
    }

    file_extensions = DotAccessDict(file_extensions)

    blob_types = {
        "block_blob": "BlockBlob",
    }

    blob_types = DotAccessDict(blob_types)

    keys_of_key_vault_secrets = {
        "azure_queue_conn_string": "AzureQueueConnString",
        "app_insights_conn_string": "AppInsightsConnString",
        "queue_name": "QueueName",
        "blob_storage_base_uri": "BlobStorageBaseUri",
        "azure_vision_ai_endpoint": "AzureVisionAiEndpoint",
        "azure_vision_ai_key": "AzureVisionAiKey",
        "blob_storage_conn_string": "BlobStorageConnString",
        "blob_storage_container_name": "BlobStorageContainerName",
        "sharepoint_client_id": "SharepointClientId",
        "sharepoint_tenant_id": "SharepointTenantId",
        "sharepoint_client_secret": "SharepointClientSecret",
        "basic_auth_username": "BasicAuthUsername",
        "basic_auth_password": "BasicAuthPassword",
        "basic_auth_realm": "BasicAuthRealm",
        "mysql_username": "MysqlUsername",
        "mysql_password": "MysqlPassword",
        "mysql_host": "MysqlHost",
        "mysql_port": "MysqlPort",
        "mysql_database": "MysqlDatabase",
        "pgvector_username": "PgVectorUsername",
        "pgvector_password": "PgVectorPassword",
        "pgvector_host": "PgVectorHost",
        "pgvector_port": "PgVectorPort",
        "pgvector_database": "PgVectorDatabase",
        "azure_openai_endpoint": "AzureOpenAIEndpoint",
        "azure_openai_deployment_name": "AzureOpenAIDeploymentName",
        "azure_openai_key": "AzureOpenAIKey",
        "azure_openai_version": "AzureOpenAIVersion",
    }

    keys_of_key_vault_secrets = DotAccessDict(keys_of_key_vault_secrets)
