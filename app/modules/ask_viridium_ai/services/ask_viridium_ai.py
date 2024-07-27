import time

from langchain_core.runnables import Runnable
from openai import BadRequestError

from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_community.callbacks import get_openai_callback
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser

from app.modules.ask_viridium_ai.constants import AskViridiumConstants
from app.modules.ask_viridium_ai.models import MaterialComposition, MaterialInfo

from utils.exceptions import (
    LLMInteractionError,
    PromptInitError,
    FunctionCreationError,
    FunctionBindingError,
)


class AskViridium:
    def __init__(self, logger, global_constants):
        self.logger = logger
        self.constants = AskViridiumConstants()

        llm = AzureChatOpenAI(
            deployment_name=global_constants.azure_openai_chat_model_deployment_name,
            temperature=self.constants.temperature,
            max_tokens=self.constants.max_tokens,
            timeout=self.constants.timeout,
        )

        # Initialize prompts and functions
        chem_info_prompt = self.chem_info_prompt_init()
        material_analysis_prompt = self.material_analysis_prompt_init()

        # Create OpenAI functions
        chem_info_function, material_analysis_function = (
            self.openai_functions_creation()
        )

        # Bind functions to models
        chem_info_model, material_analysis_model = self.bind_function(
            llm, chem_info_function, material_analysis_function
        )

        # Initialize JSON output parser
        parser = JsonOutputFunctionsParser()

        # Defining Chains as class attributes
        self.chem_info_chain = chem_info_prompt | chem_info_model | parser
        self.material_analysis_chain = (
            material_analysis_prompt | material_analysis_model | parser
        )

    def chem_info_prompt_init(self) -> ChatPromptTemplate:
        """
        Initialize the prompt for chemical information by combining system and human prompts.

        Returns:
            ChatPromptTemplate: The prompt template for finding chemical composition of the material provided.
        """
        try:
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self.constants.material_composition_system_prompt),
                    ("human", self.constants.material_composition_human_prompt),
                ]
            )
            return prompt
        except Exception as e:
            self.logger.error(e)
            raise PromptInitError(
                details=f"Error during initialization of chemical information prompt: {e}"
            )

    def material_analysis_prompt_init(self) -> ChatPromptTemplate:
        """
        Initialize the prompt for analysis by combining system and human prompts.

        Returns:
            ChatPromptTemplate: The prompt template for analysis.
        """
        try:
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", self.constants.material_analysis_system_prompt),
                    ("human", self.constants.material_analysis_human_prompt),
                ]
            )
            return prompt
        except Exception as e:
            self.logger.exception(e)
            raise PromptInitError(
                details=f"Error during initialization of material analysis prompt: {e}"
            )

    def openai_functions_creation(self) -> (list, list):
        """
        Create OpenAI functions for chemical composition and analysis by converting Pydantic objects.

        Returns:
            list: A list containing the chemical info function and analysis function.
        """
        try:
            chem_info_function = [convert_to_openai_function(MaterialComposition)]
            analysis_function = [convert_to_openai_function(MaterialInfo)]
            self.logger.info("OpenAI Functions created successfully.")
            return chem_info_function, analysis_function
        except Exception as e:
            self.logger.exception(f"Error while creating OpenAI functions: {e}")
            raise FunctionCreationError(
                details=f"Error while converting Pydantic object to OpenAI functions: {e}"
            )

    def bind_function(
        self, llm, chem_info_function, material_analysis_function
    ) -> (Runnable, Runnable):
        """
        Bind functions to the LLM for function calling and specify models to be used.

        Returns:
            list: a list of models of material composition and of performing the PFAS analysis
        """
        try:
            # Bind the chemical analysis function to the LLM
            chem_info_model = llm.bind_functions(
                functions=chem_info_function,
                function_call={"name": "MaterialComposition"},
            )

            # Bind the analysis function to the LLM
            analysis_model = llm.bind_functions(
                functions=material_analysis_function,
                function_call={"name": "MaterialInfo"},
            )
            self.logger.info("Bound functions to model successfully.")
            return chem_info_model, analysis_model
        except Exception as e:
            self.logger.exception(f"Exception while binding openai functions: {e}")
            raise FunctionBindingError(
                details=f"Error while binding function to LLM instance: {e}"
            )

    def query(self, material_name: str, manufacturer_name: str) -> dict[str, str]:
        """
        Uses OpenAI function calling and output parsing to generate a structured PFAS analysis.

        Args:
            :type material_name: str
            :type manufacturer_name: str
        Returns:
            str: The result of the material's analysis.
            :param self:
        """
        start = time.perf_counter()

        # for logging purposes
        query_parameters = {
            "custom_dimensions": {
                "material": material_name,
                "manufacturer": manufacturer_name,
            }
        }
        self.logger.info(f"Received query", extra=query_parameters)

        # Extracting material composition information
        tokens_for_chem_info = 0
        cost_for_chem_info = 0
        chemicals_list = None
        try:
            # Using callbacks for getting token usage and cost info
            with get_openai_callback() as cb:
                self.logger.info(
                    "Invoking chemical information chain", extra=query_parameters
                )

                # Invoke the chemical info chain and get the chemical composition.

                # The example (line 193) is provided here instead of within the prompt because Langchain AzureChatOpenAI
                # uses f-strings for its methods.
                # When we pass a dictionary as the example, AzureChatOpenAI expects the keys in the dictionary to be
                # parameters within the f-string, leading to errors. Thus, the example is included directly in the code.
                material_composition = self.chem_info_chain.invoke(
                    {
                        "material": material_name,
                        "example": self.constants.chemical_composition_example,
                    }
                )

                self.logger.info(
                    f"Chemical composition received: {material_composition}",
                    extra=query_parameters,
                )

                # Extracting names of chemicals comprising the material and storing in chemicals_list to pass to
                # second chain.
                chemicals_list = [
                    chemical["name"] for chemical in material_composition["chemicals"]
                ]

                tokens_for_chem_info = cb.total_tokens
                cost_for_chem_info = cb.total_cost

        except BadRequestError as e:
            self.logger.error(
                "OpenAI BadRequestError during chemical composition retrieval: %s",
                e,
                extra=query_parameters,
            )

            # chemicals_list is being initialized as an empty list instead of raising an error here, because we
            # can still generate a PFAS analysis just based on the material and manufacturer names. If the
            # invoke call fails, we shouldn't need to bring the whole service down
            chemicals_list = []

        except Exception as e:
            self.logger.exception(
                "Unexpected error during chemical composition retrieval: %s",
                e,
                extra=query_parameters,
            )

            # chemicals_list is being initialized as an empty list instead of raising an error here, because we
            # can still generate a PFAS analysis just based on the material and manufacturer names. If the
            # invoke call fails, we shouldn't need to bring the whole service down
            chemicals_list = []

        # PFAS Analysis
        tokens_for_material_analysis = 0
        cost_for_material_analysis = 0
        result = dict()
        try:
            with get_openai_callback() as cb:
                self.logger.info("Invoking analysis chain", extra=query_parameters)

                # Invoke the analysis chain and get the analysis result

                # The example (line 254) is provided here instead of within the prompt because Langchain AzureChatOpenAI
                # uses f-strings for its methods.
                # When we pass a dictionary as the example, AzureChatOpenAI expects the keys in the dictionary to be
                # parameters within the f-string, leading to errors. Thus, the example is included directly in the code.
                result = self.material_analysis_chain.invoke(
                    {
                        "material": material_name,
                        "manufacturer": manufacturer_name,
                        "chemical_composition": chemicals_list,
                        "example": self.constants.material_analysis_example,
                    }
                )

                self.logger.info(
                    "Analysis generated successfully.", extra=query_parameters
                )

                tokens_for_material_analysis = cb.total_tokens
                cost_for_material_analysis = cb.total_cost

        except BadRequestError as e:
            self.logger.error(
                "OpenAI BadRequestError during analysis: %s", e, extra=query_parameters
            )
            result["decision"] = "OpenAI BadRequestError during analysis"
            raise LLMInteractionError(details=f"OpenAI BadRequestError: {e}")
        except Exception as e:
            self.logger.exception(
                "Unexpected error during analysis: %s", e, extra=query_parameters
            )
            result["decision"] = "Unexpected error during analysis"
            raise LLMInteractionError(details=f"Unexpected error: {e}")

        duration = time.perf_counter() - start

        analysis_log = {
            "material_composition": chemicals_list,
            "result": result,
        }

        # these entries will be added in customDimensions in Application Insights so that costs, time, etc. can
        # be tracked. Moreover, these will help us create interesting plots in the App Insights dashboard.
        analysis_details = {
            "custom_dimensions": {
                "duration(seconds)": duration,
                "material": material_name,
                "manufacturer": manufacturer_name,
                "tokens_used_for_chemical_composition": tokens_for_chem_info,
                "tokens_used_for_material_analysis": tokens_for_material_analysis,
                "cost_for_chemical_composition": cost_for_chem_info,
                "cost_for_material_analysis": cost_for_material_analysis,
                "total_cost": cost_for_chem_info + cost_for_material_analysis,
                "total_tokens": tokens_for_material_analysis + tokens_for_chem_info,
                "PFAS_analysis": result["decision"],
            },
        }
        self.logger.info(analysis_log, extra=analysis_details)

        return result
