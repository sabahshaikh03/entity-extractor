from dotenv import load_dotenv

load_dotenv()

from flask import Flask, request
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from connectors.key_vault_connector import AzureKeyVaultConnector
from global_constants import GlobalConstants
from utils.threading_tools import ThreadingTool
from app.modules.keyword_analysis.constants import KeywordAnalysisConstants
from utils.logger import Logging
from app.modules.keyword_analysis.routes import MainRoutes
from processors.queue import QueueProcessor

constants = KeywordAnalysisConstants
global_constants = GlobalConstants
kv_client = AzureKeyVaultConnector()
threading_tool = ThreadingTool

app_insights_connector = Logging()
logger = app_insights_connector.get_logger()

queue_processor = QueueProcessor(logger=logger)

app = Flask(__name__)

# App Config
CORS(app)
app.config[global_constants.basic_auth_parameters.basic_auth_username] = (
    kv_client.get_secret(global_constants.keys_of_key_vault_secrets.basic_auth_username)
)
app.config[global_constants.basic_auth_parameters.basic_auth_password] = (
    kv_client.get_secret(global_constants.keys_of_key_vault_secrets.basic_auth_password)
)
app.config[global_constants.basic_auth_parameters.basic_auth_realm] = (
    kv_client.get_secret(global_constants.keys_of_key_vault_secrets.basic_auth_realm)
)


# Logging
@app.before_request
def log_request_info():
    logger.info(f"API REQUEST : {request.method} {request.path}")


@app.after_request
def log_response_info(response):
    logger.info(f"API RESPONSE : {response.status}")
    return response


# Rgister routes blueprint
main_routes = MainRoutes(logger, app)
app.register_blueprint(main_routes.blueprint, url_prefix=GlobalConstants.api_version)

# Register swagger blueprint
swagger_endpoint = global_constants.swagger_endpoint
swaggerui_blueprint = get_swaggerui_blueprint(
    swagger_endpoint,
    global_constants.swagger_json_api_endpoint,
    config={"app_name": global_constants.swagger_app_name},
)
app.register_blueprint(swaggerui_blueprint, url_prefix=swagger_endpoint)


# Create 20 threads to process waiting api calls from queue
threads = threading_tool.create_and_start_threads(
    queue_processor.process_waiting_queue_items,
    num_threads=global_constants.no_of_threads,
    daemon=True,
)
