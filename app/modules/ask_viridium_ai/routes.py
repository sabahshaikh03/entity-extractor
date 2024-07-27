from flask import Blueprint, request, Response
from typing import Any
from werkzeug.exceptions import HTTPException

from app.modules.ask_viridium_ai.services.ask_viridium_ai import AskViridium
from marshmallow import Schema, fields

from utils.basic_auth import BasicAuth
from functools import wraps
from utils.request_response_utility import return_api_response, validate_request_data
from .constants import AskViridiumInputParameters


class AskVAISchema(Schema):
    material_name = fields.Str(required=True)
    manufacturer_name = fields.Str(required=False)


class AskAIRoutes:
    def __init__(self, logger, global_constants):  # add self.logger here
        self.logger = logger
        self.blueprint = Blueprint("ask_viridium_ai_routes", __name__)

        self.global_constants = global_constants
        self.input_parameters = AskViridiumInputParameters().input_parameters
        self.basic_auth = BasicAuth(self.global_constants)

        self.blueprint.add_url_rule(
            "/ask-viridium-ai",
            view_func=self.basic_auth.required(self.ask_viridium_ai),
            methods=[self.global_constants.rest_api_methods.post],
        )
        self.ask_vai = AskViridium(self.logger, self.global_constants)

    # @basic_auth.required
    def ask_viridium_ai(self) -> tuple[Response, Any]:
        """
        ---
        post:
          summary: Handles AI query requests.
          requestBody:
            required: true
            content:
              application/json:
                schema: AskVAISchema
          responses:
            200:
              description: Analysis completed successfully
            400:
              description: Bad request
            500:
              description: Internal server error
        """
        try:
            request_data = request.get_json()

            required_params = [self.input_parameters.material_name]

            missing_params = validate_request_data(
                request_data, required_params, self.logger
            )
            if missing_params:
                return return_api_response(
                    self.global_constants.api_status_codes.bad_request,
                    self.global_constants.api_response_messages.missing_required_parameters,
                    self.logger,
                    self.global_constants,
                    f"{self.global_constants.api_response_parameters.missing_parameters}: {missing_params}",
                )

            try:
                result = self.ask_vai.query(
                    request_data.get(self.input_parameters.material_name),
                    request_data.get(self.input_parameters.manufacturer_name),
                )

                return return_api_response(
                    self.global_constants.api_status_codes.ok,
                    self.global_constants.api_response_messages.success,
                    self.logger,
                    self.global_constants,
                    result,
                )

            except Exception as e:
                self.logger.exception(e)
                return return_api_response(
                    self.global_constants.api_status_codes.internal_server_error,
                    "Error while running query method in Ask Viridium AI class.",
                    self.logger,
                    self.global_constants,
                )

        except HTTPException as e:
            self.logger.error(f"HTTP exception: {e}")
            return return_api_response(
                e.code, str(e), self.logger, self.global_constants
            )

        except Exception as e:
            self.logger.exception(f"Unhandled exception occurred: {e}")
            return return_api_response(
                self.global_constants.api_status_codes.internal_server_error,
                "An unexpected error occurred. Please try again later.",
                self.logger,
                self.global_constants,
            )
