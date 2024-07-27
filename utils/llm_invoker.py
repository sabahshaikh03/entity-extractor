import os
from langchain.prompts import ChatPromptTemplate
from langchain_community.callbacks import get_openai_callback
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_openai import AzureChatOpenAI
from langchain_openai.embeddings import AzureOpenAIEmbeddings
from sqlalchemy.orm import Session

from app.modules.entity_extractor.constants import EntityExtractorConstants
from app.modules.entity_extractor.models.material_models import Material, Chemical
from common.models.vector import Vector
from connectors.key_vault_connector import AzureKeyVaultConnector
from global_constants import GlobalConstants
from utils.threading_tools import ThreadingTool

from sqlalchemy import create_engine, Column, Integer, String, Text, BigInteger, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

global_constants = GlobalConstants
constants = EntityExtractorConstants()


class LLMInvoker:
    def __init__(self, logger, session: Session):
        self.logger = logger
        self.session = session
        self.thread_id = ThreadingTool.get_thread_id()

        engine = create_engine(
            f'postgresql://{constants.pg_user}:{constants.pg_password}@{constants.pg_host}:{constants.pg_port}/{constants.pg_dbname}'
        )
        Base.metadata.create_all(engine)
        self.Session = sessionmaker(bind=engine)

        try:
            # Initialize Key Vault client (commented out for now)
            # kv_client = AzureKeyVaultConnector()
            # llm_deployment = kv_client.get_secret(global_constants.keys_of_key_vault_secrets.llm_deployment)
            # azure_openai_api_key = kv_client.get_secret(global_constants.keys_of_key_vault_secrets.azure_openai_api_key)
            # azure_openai_endpoint = kv_client.get_secret(global_constants.keys_of_key_vault_secrets.azure_openai_endpoint)

            self.embedding_function = AzureOpenAIEmbeddings(
                deployment=constants.embedding_deployment,
                api_key=constants.azure_openai_api_key,
                azure_endpoint=constants.azure_openai_endpoint
            )

            self.llm_instance = AzureChatOpenAI(
                deployment_name=constants.llm_deployment,
                api_key=constants.azure_openai_api_key,
                azure_endpoint=constants.azure_openai_endpoint
            )
            self.logger.info(f"LLMInvoker : {self.thread_id} ::  LLM Invocation Initialized Successfully.")
        except Exception as e:
            self.logger.error(f"LLMInvoker: {self.thread_id} :: : {e}")

        # Convert Pydantic models to OpenAI-compatible functions
        self.material_info_extractor_function = [convert_to_openai_function(Material)]
        self.material_composition_extractor = [convert_to_openai_function(Chemical)]

        # Bind models to language models
        self.material_info_model = self.llm_instance.bind_functions(
            functions=self.material_info_extractor_function,
            function_call={"name": "Material"}
        )
        self.material_composition_model = self.llm_instance.bind_functions(
            functions=self.material_composition_extractor,
            function_call={"name": "Chemical"}
        )
        self.logger.info(f"LLMInvoker : {self.thread_id} :: : Binding OpenAI functions completed successfully.")

        # Set up material_extraction_prompt
        self.material_extraction_prompt = ChatPromptTemplate.from_messages(
            [("system", constants.template), ("human", constants.human_query)]
        )
        self.logger.info(f"LLMInvoker : {self.thread_id} :: : Prompt template initialized.")

        # Set up parser
        self.json_parser = JsonOutputFunctionsParser()

        # Set up sections to extract
        self.sections = [
            ("Material", self.material_extraction_prompt | self.material_info_model | self.json_parser, constants.identification_prompt),
            ("Chemical", self.material_extraction_prompt | self.material_composition_model | self.json_parser, constants.chemical_composition_prompt)
        ]
        self.logger.info(f"LLMInvoker : {self.thread_id} :: : Sections to extract set up.")

    def set_session(self, session: Session):
        self.session = session

    def run(self, artifact_id):
        results = dict()
        print("Extracting information: ")
        for name, chain, section in self.sections:
            try:
                result, cost, tokens = self.process_query(chain, section, artifact_id)
                results[name] = result
            except Exception as e:
                print("EXCEPTION: ", e)

        return results

    def process_query(self, chain, query, artifact_id):
        print("Received query: ", query)
        session = self.Session()
        embedding = self.embedding_function.embed_query(query)
        docs = session.query(Vector.text).filter(Vector.file_id == artifact_id).order_by(Vector.embedding.l2_distance(embedding)).all()
        doc_contents = [doc.text for doc in docs]
        print("Retrieved documents: ", doc_contents)
        with get_openai_callback() as cb:
            # Run the chain
            result = chain.invoke({"docs": doc_contents, "query": query, "example": constants.example})
            self.logger.info(f"OpenAI result: {result}")
            print(f"OpenAI result: {result}")
            self.logger.info(f"Received result from OpenAI. Total cost: {cb.total_cost}; Total tokens: {cb.total_tokens}")
            print(f"Received result from OpenAI. Total cost: {cb.total_cost}; Total tokens: {cb.total_tokens}")
            return result, cb.total_cost, cb.total_tokens
