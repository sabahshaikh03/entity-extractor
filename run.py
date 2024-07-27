from flask_cors import CORS
from flask import Flask, request
from flask_swagger_ui import get_swaggerui_blueprint

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin

from global_routes import GlobalRoutes
from utils.logger import Logging
from utils.thread_manager import ThreadManager
from connectors.key_vault_connector import AzureKeyVaultConnector
from app.modules.keyword_analysis.routes import KeywordAnalysisRoutes
from app.modules.ask_viridium_ai.routes import AskAIRoutes
from app.modules.keyword_analysis.services.queue_service import QueueService
from global_constants import GlobalConstants


# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize constants and services
global_constants = GlobalConstants
kv_client = AzureKeyVaultConnector(global_constants)
thread_manager = ThreadManager

logger = Logging(global_constants).get_logger()

queue_service = QueueService(logger=logger, global_constants=global_constants)

# App Config
app.config.update(
    {
        global_constants.basic_auth_parameters.basic_auth_username: kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.basic_auth_username
        ),
        global_constants.basic_auth_parameters.basic_auth_password: kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.basic_auth_password
        ),
        global_constants.basic_auth_parameters.basic_auth_realm: kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.basic_auth_realm
        ),
    }
)

spec = APISpec(
    title=global_constants.apispec_config.title,
    version=global_constants.apispec_config.version,
    openapi_version=global_constants.apispec_config.openapi_version,
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)


# Logging
@app.before_request
def log_request_info():
    logger.info(f"API REQUEST : {request.method} {request.path}")


@app.after_request
def log_response_info(response):
    logger.info(f"API RESPONSE : {response.status}")
    return response


# Register routes blueprint

# Keyword Analysis Service
kwa_blueprint = KeywordAnalysisRoutes(logger, global_constants).blueprint

# Ask Viridium AI Service
askai_blueprint = AskAIRoutes(logger, global_constants).blueprint

# Swagger UI
swaggerui_blueprint = get_swaggerui_blueprint(
    global_constants.swagger_endpoint,
    global_constants.swagger_json_api_endpoint,
    config={"app_name": global_constants.swagger_app_name},
)

global_routes_blueprint = GlobalRoutes(
    logger, app, global_constants, spec=spec
).blueprint

app.register_blueprint(kwa_blueprint, url_prefix=global_constants.api_version)
app.register_blueprint(askai_blueprint, url_prefix=global_constants.api_version)
app.register_blueprint(global_routes_blueprint, url_prefix=global_constants.api_version)
app.register_blueprint(swaggerui_blueprint)

# Create and start threads for processing API calls
threads = thread_manager.create_and_start_threads(
    queue_service.process_waiting_api_calls,
    num_threads=global_constants.no_of_threads,
    daemon=True,
)

# Run the app
if __name__ == "__main__":
    app.run(
        threaded=True,
        debug=False,  # Disable debug mode for production
        port=global_constants.flask_app_port,
        host=global_constants.flask_host,
    )
