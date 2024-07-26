# Utility for invoking a Large Language Model (LLM)
import os
from langchain.prompts import ChatPromptTemplate
from langchain_community.callbacks import get_openai_callback
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_openai import AzureChatOpenAI
from sqlalchemy.orm import Session

from app.modules.entity_extractor.constants import EntityExtractorConstants
from app.modules.entity_extractor.models.material_models import Material, Chemical
from connectors.key_vault_connector import AzureKeyVaultConnector
from global_constants import GlobalConstants
from utils.threading_tools import ThreadingTool

constants = EntityExtractorConstants
global_constants = GlobalConstants


class LLMInvoker:
    def __init__(self, logger, session: Session):
        self.logger = logger
        self.session = session
        self.thread_id = ThreadingTool.get_thread_id()
        self.llm_instance = None  # Initialize llm_instance as None

        try:
            # Initialize Key Vault client
            # kv_client = AzureKeyVaultConnector()
            # llm_deployment = kv_client.get_secret(global_constants.keys_of_key_vault_secrets.llm_deployment)
            # azure_openai_api_key = kv_client.get_secret(global_constants.keys_of_key_vault_secrets.azure_openai_api_key)
            # azure_openai_endpoint = kv_client.get_secret(global_constants.keys_of_key_vault_secrets.azure_openai_endpoint)

            # environment variables instead
            llm_deployment = os.getenv('LLM_DEPLOYMENT')
            azure_openai_api_key = os.getenv('AZURE_OPENAI_API_KEY')
            azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')

            self.llm_instance = AzureChatOpenAI(
                deployment_name=llm_deployment,
                api_key=azure_openai_api_key,
                azure_endpoint=azure_openai_endpoint
            )
            self.logger.info(f"LLMInvoker : {self.thread_id} ::  LLM Invocation Initialized Successfully.")

        except Exception as e:
            self.logger.error(f"LLMInvoker: {self.thread_id} :: : {e}")

        if self.llm_instance:
            # Convert Pydantic models to OpenAI-compatible functions
            self.material_extractor = [convert_to_openai_function(Material)]
            self.material_composition_extractor = [convert_to_openai_function(Chemical)]

            # Bind models to language models
            self.material_model = self.llm_instance.bind_functions(functions=self.material_extractor,
                                                                   function_call={"name": "Material"})
            self.material_composition_model = self.llm_instance.bind_functions(
                functions=self.material_composition_extractor,
                function_call={"name": "Chemical"})

            self.logger.info(f"LLMInvoker : {self.thread_id} :: : Binding OpenAI functions completed successfully.")

            # Set up material_extraction_prompt
            self.material_extraction_prompt = ChatPromptTemplate.from_messages([
                ("system", constants.template),
                ("human", constants.human_query)
            ])
            self.logger.info(f"LLMInvoker : {self.thread_id} :: : Prompt template initialized.")

            # Set up parser
            self.json_parser = JsonOutputFunctionsParser()

            # Set up sections to extract
            self.sections = [
                ("Material", self.material_extraction_prompt | self.material_model | self.json_parser,
                 constants.material_prompt),
                ("chemicals", self.material_extraction_prompt | self.material_composition_model | self.json_parser,
                 constants.chemical_composition_prompt),
            ]
            self.logger.info(f"LLMInvoker : {self.thread_id} :: : Sections to extract set up.")
        else:
            self.logger.error(f"LLMInvoker : {self.thread_id} :: : LLM instance initialization failed.")

    def get_material_info(self, doc_contents, query, chain):
        with get_openai_callback() as cb:
            result = chain.invoke({"docs": doc_contents, "query": query, "example": constants.example})
            self.logger.info(f"OpenAI result: {result}")
            self.logger.info(
                f"Received result from OpenAI. Total cost: {cb.total_cost}; Total tokens: {cb.total_tokens}")
            return result, cb.total_cost, cb.total_tokens
