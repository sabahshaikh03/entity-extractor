from flask import Blueprint, jsonify, request
from marshmallow import Schema, fields
from app.modules.keyword_analysis.services.keywords_service import KeywordsService
from app.modules.keyword_analysis.constants import KeywordAnalysisConstants
from app.modules.keyword_analysis.services.file_analysis_service import (
    FileAnalysisService,
)
from azure.core.exceptions import ResourceNotFoundError
from utils.basic_auth import BasicAuth


class SearchKeywordsSchema(Schema):
    file_uri = fields.Str(required=True)
    source = fields.Str(required=True)
    keywords = fields.List(fields.Str(), required=False)
    search_scope = fields.Str(required=False)
    force = fields.Bool(required=False)


class StoreKeywordsSchema(Schema):
    id = fields.Str(required=True)
    keywords = fields.List(fields.Str(), required=True)


class KeywordAnalysisRoutes:
    def __init__(self, logger, global_constants):
        self.constants = KeywordAnalysisConstants
        self.global_constants = global_constants

        self.blueprint = Blueprint("main_routes", __name__)
        self.file_analysis_service = FileAnalysisService(logger, self.global_constants)
        self.keywords_service = KeywordsService(logger, self.global_constants)
        self.logger = logger
        self.basic_auth = BasicAuth(self.global_constants)

        self.blueprint.add_url_rule(
            "/search-in-document",
            view_func=self.basic_auth.required(self.search_keywords),
            methods=[self.global_constants.rest_api_methods.post],
        )
        self.blueprint.add_url_rule(
            "/keywords",
            view_func=self.basic_auth.required(self.store_keywords),
            methods=[self.global_constants.rest_api_methods.post],
        )
        self.blueprint.add_url_rule(
            "/keywords",
            view_func=self.basic_auth.required(self.get_keywords),
            methods=[self.global_constants.rest_api_methods.get_api],
        )
        self.blueprint.add_url_rule(
            "/search-in-document/status",
            view_func=self.basic_auth.required(self.get_status_of_file_analysis),
            methods=[self.global_constants.rest_api_methods.get_api],
        )

    def return_api_response(self, status, message, result=None, additional_data=None):
        response_data = {
            self.global_constants.api_response_parameters.status: status,
            self.global_constants.api_response_parameters.message: message,
            self.global_constants.api_response_parameters.result: result,
        }
        if additional_data:
            response_data.update(additional_data)

        return jsonify(response_data), status

    def validate_request_data(self, request_data, required_params):
        missing_params = [
            param for param in required_params if param not in request_data
        ]
        if missing_params:
            return False, missing_params
        return True, None

    def search_keywords(self):
        """
        ---
        post:
          summary: Search keywords in a document
          requestBody:
            required: true
            content:
              application/json:
                schema: SearchKeywordsSchema
          responses:
            200:
              description: Search results
            400:
              description: Bad request
            500:
              description: Internal server error
        """
        try:
            request_data = request.get_json()
            required_params = [
                self.constants.api_parameters.file_uri,
                self.constants.api_parameters.source,
            ]
            valid_request, missing_params = self.validate_request_data(
                request_data, required_params
            )
            if not valid_request:
                return self.return_api_response(
                    self.global_constants.api_status_codes.bad_request,
                    self.global_constants.api_response_messages.missing_required_parameters,
                    f"{self.global_constants.api_response_parameters.missing_parameters}: {missing_params}",
                )

            # Extract parameters from the request body
            keywords_to_search = request_data.get(
                self.constants.api_parameters.keywords, []
            )
            file_uri = request_data.get(self.constants.api_parameters.file_uri)

            self.logger.info(f"File received : {file_uri}")

            source = request_data.get(self.constants.api_parameters.source)
            search_scope = request_data.get(
                self.constants.api_parameters.search_scope,
                self.constants.search_scopes.default,
            )
            force = request_data.get(self.constants.api_parameters.force, False)

            response_data = self.file_analysis_service.enqueue_api_request(
                file_uri=file_uri,
                search_scope=search_scope,
                input_file_source=source,
                local_keywords=keywords_to_search,
                force=force,
            )

            if (
                self.global_constants.api_response_parameters.identifier
                in response_data
            ):
                return self.return_api_response(
                    response_data[self.global_constants.api_response_parameters.status],
                    response_data[
                        self.global_constants.api_response_parameters.message
                    ],
                    {
                        self.global_constants.api_response_parameters.identifier: response_data[
                            self.global_constants.api_response_parameters.identifier
                        ]
                    },
                )
            else:
                return self.return_api_response(
                    response_data[self.global_constants.api_response_parameters.status],
                    response_data[
                        self.global_constants.api_response_parameters.message
                    ],
                )
        except Exception as e:
            self.logger.exception(f"POST API /search-in-document :: Error : {str(e)}")
            return self.return_api_response(
                self.global_constants.api_status_codes.internal_server_error,
                str(e),
            )

    def store_keywords(self):
        """
        ---
        post:
          summary: Store keywords
          requestBody:
            required: true
            content:
              application/json:
                schema: StoreKeywordsSchema
          responses:
            200:
              description: Keywords stored successfully
            400:
              description: Bad request
            500:
              description: Internal server error
        """
        try:
            request_data = request.get_json()
            required_params = [
                self.constants.api_parameters.id,
                self.constants.api_parameters.keywords,
            ]
            valid_request, missing_params = self.validate_request_data(
                request_data, required_params
            )

            if not valid_request:
                return self.return_api_response(
                    self.global_constants.api_status_codes.bad_request,
                    self.global_constants.api_response_messages.missing_required_parameters,
                    {
                        self.global_constants.api_response_parameters.missing_parameters: missing_params
                    },
                )

            id = request_data[self.constants.api_parameters.id]
            keywords = request_data[self.constants.api_parameters.keywords]

            self.keywords_service.store_keywords(id, keywords)

            # Return a success response
            return self.return_api_response(
                self.global_constants.api_status_codes.ok,
                self.global_constants.api_response_messages.success,
            )
        except Exception as e:
            self.logger.exception(f"POST API /keywords :: {str(id)} - Error : {str(e)}")
            return self.return_api_response(
                self.global_constants.api_status_codes.internal_server_error,
                str(e),
            )

    def get_keywords(self):
        """
        ---
        get:
          summary: Get keywords
          responses:
            200:
              description: Keywords retrieved successfully
            400:
              description: Bad request
            500:
              description: Internal server error
        """
        try:
            id = self.keywords_service.get_keywords_id()

            # If global keywords is not configured return error message
            if id is None:
                return self.return_api_response(
                    self.global_constants.api_status_codes.bad_request,
                    self.global_constants.api_response_messages.global_keywords_not_configured,
                )

            # Return a success response
            return self.return_api_response(
                self.global_constants.api_status_codes.ok,
                self.global_constants.api_response_messages.success,
                {self.global_constants.api_response_parameters.id: id},
            )
        except ResourceNotFoundError:
            return self.return_api_response(
                self.global_constants.api_status_codes.bad_request,
                self.global_constants.api_response_messages.global_keywords_not_found,
            )
        except Exception as e:
            self.logger.exception(f"GET API /keywords :: {str(id)} - Error : {str(e)}")
            return self.return_api_response(
                self.global_constants.api_status_codes.internal_server_error,
                str(e),
            )

    def get_status_of_file_analysis(self):
        """
        ---
        get:
          summary: Get status of file analysis
          parameters:
            - name: file_identifier
              in: query
              required: true
              schema:
                type: string
          responses:
            200:
              description: Status retrieved successfully
            400:
              description: Bad request
            500:
              description: Internal server error
        """
        try:
            file_identifier = request.args.get(
                self.constants.api_parameters.file_identifier, None
            )

            if file_identifier is None:
                return self.return_api_response(
                    self.global_constants.api_status_codes.bad_request,
                    self.global_constants.api_response_messages.missing_required_parameters,
                    {
                        self.global_constants.api_response_parameters.missing_parameters: [
                            self.constants.api_parameters.file_identifier
                        ]
                    },
                )

            status, result = self.file_analysis_service.get_status_of_file(
                file_identifier
            )

            if result == self.constants.messages.invalid_file_identifier:
                return self.return_api_response(
                    self.global_constants.api_status_codes.bad_request,
                    result,
                )

            return self.return_api_response(
                self.global_constants.api_status_codes.ok, status, result
            )
        except Exception as e:
            self.logger.exception(
                f"POST API /search-in-document/status :: {str(file_identifier)} - Error : {str(e)}"
            )
            return self.return_api_response(
                self.global_constants.api_status_codes.internal_server_error,
                str(e),
            )
