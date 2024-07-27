from flask import Blueprint, jsonify

from utils.request_response_utility import return_api_response

from connectors.azure_vision_connector import AzureVisionConnector
from connectors.azure_queue_connector import AzureQueueConnector
from connectors.blob_storage_connector import AzureBlobStorageConnector
from connectors.key_vault_connector import AzureKeyVaultConnector
from connectors.sharepoint_connector import SharePointConnector


class GlobalRoutes:
    def __init__(self, logger, app, global_constants, spec):
        self.global_constants = global_constants
        self.logger = logger
        self.app = app
        self.spec = spec
        self.blueprint = Blueprint("global_routes", __name__)

        self.blueprint.add_url_rule(
            "/api/swagger.json",
            view_func=self.get_swagger_spec,
        )
        self.blueprint.add_url_rule(
            "/health",
            view_func=self.health_check,
            methods=["GET"],
        )

    def get_swagger_spec(self):
        """
        Generates the Swagger specification for the API.

        Returns:
        - The Swagger specification in JSON format.
        """
        with self.app.test_request_context():
            # for blueprint in self.blueprints:
            #     for view_func in blueprint.view_functions.values():
            #         print(view_func)
            #         spec.path(view=view_func)

            for rule in self.app.url_map.iter_rules():
                try:
                    self.spec.path(view=self.app.view_functions[rule.endpoint])
                except Exception as e:
                    pass

        return jsonify(self.spec.to_dict())

    def health_check(self):
        """
        ---
        get:
          summary: Health check
          responses:
            200:
              description: Server is running
        """

        return return_api_response(
            self.global_constants.api_status_codes.ok,
            self.global_constants.api_response_messages.server_is_running,
            self.logger,
            self.global_constants,
        )
