from flask import Blueprint, jsonify, request
from marshmallow import Schema, fields
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from azure.core.exceptions import ResourceNotFoundError
from global_constants import GlobalConstants
from utils.basic_auth import basic_auth
from app.modules.artifact_ingestor.constants import Constants
from app.modules.artifact_ingestor.services.artifact_ingestor_service import (
    ArtifactIngestorService,
)
from app.modules.artifact_ingestor.dto.artifact_input_dto import ArtifactInputDTO
from utils.exceptions import CommonException
from pydantic import ValidationError


class SearchKeywordsSchema(Schema):
    file_uri = fields.Str(required=True)
    source = fields.Str(required=True)
    keywords = fields.List(fields.Str(), required=False)
    search_scope = fields.Str(required=False)
    force = fields.Bool(required=False)


class StoreKeywordsSchema(Schema):
    id = fields.Str(required=True)
    keywords = fields.List(fields.Str(), required=True)


class MainRoutes:
    def __init__(self, logger, app):
        self.blueprint = Blueprint("artifact_ingestor_routes", __name__)
        self.artifact_ingestor_service = ArtifactIngestorService(
            logger=logger, asyncio_event_loop=None
        )
        self.constants = Constants
        self.global_constants = GlobalConstants
        self.logger = logger
        self.app = app

        self.blueprint.add_url_rule(
            "/add-artifact",
            view_func=self.add_artifact,
            methods=[self.global_constants.rest_api_methods.post],
        )

        self.blueprint.add_url_rule(
            "/api/swagger.json",
            view_func=self.get_swagger_specs,
            methods=[self.global_constants.rest_api_methods.get_api],
        )

    def get_swagger_specs(self):
        # Swagger and APISpec setup
        spec = APISpec(
            title=self.global_constants.apispec_config.title,
            version=self.global_constants.apispec_config.version,
            openapi_version=self.global_constants.apispec_config.openapi_version,
            plugins=[FlaskPlugin(), MarshmallowPlugin()],
        )
        with self.app.test_request_context():
            for view in [
                self.search_keywords,
                self.store_keywords,
                self.get_keywords,
                self.get_status_of_file_analysis,
                self.health_check,
            ]:
                spec.path(view=view)

        return jsonify(spec.to_dict())

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

    """
        ---
        post:
          summary: Add an artifact and analyze MSDS
          requestBody:
            required: true
            content:
              application/json:
                schema: ArtifactInputDTO
          responses:
            200:
              description: Artifact added successfully
            400:
              description: Bad request
            500:
              description: Internal server error
    """
    @basic_auth.required
    def add_artifact(self):
        try:
            # Parse the request JSON into the ArtifactInputDTO
            data = request.get_json()
            artifact_input_data = ArtifactInputDTO(**data)
        except ValidationError as e:
            # Return a 400 response if validation fails
            return self.return_api_response(400, "Invalid input data", result=str(e))

        try:
            # Call the service to add the artifact
            artifact = self.artifact_ingestor_service.add_artifact(artifact_input_data)

            # Analyze MSDS for the artifact
            msds_analysis = self.artifact_ingestor_service.analyze_msds(
                artifact, artifact_input_data.file_url
            )

            # Save the MSDS analysis results
            material = self.artifact_ingestor_service.save_msds(msds_analysis)

            # Return the artifact id
            return self.return_api_response(
                200, "Artifact added successfully", result={"material_id": material.id}
            )

        except CommonException as e:
            # Return a 400 response for common exceptions
            return self.return_api_response(400, str(e))

        except ResourceNotFoundError as e:
            # Return a 404 response if a resource is not found
            return self.return_api_response(404, "Resource not found", result=str(e))

        except Exception as e:
            # Return a 500 response for any other exceptions
            return self.return_api_response(500, "Internal server error", result=str(e))
