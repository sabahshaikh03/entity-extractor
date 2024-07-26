from utils.dot_access_dict import DotAccessDict
from utils.import_resources import import_string_resource


# TODO: make the blob constants global
class EntityExtractorConstants(DotAccessDict):
    def __init__(self):
        super().__init__()
        self.pkg = "app.modules.entity_extractor.resources"

        # creating root directory reference for examples (app.modules.entity_extractor.resources)
        self.examples = f"{self.pkg}.examples"
        self.examples_files = {
            "chemical": "chemical_example.json",
            "material": "material_example.json",
        }

        # creating root directory reference for system prompt templates (app.modules.entity_extractor.resources)
        self.system = f"{self.pkg}.system_prompt_templates"
        self.system_prompts_files = {
            "material": "material_system_prompt.txt",
        }

        # creating root directory reference for human prompt templates (app.modules.entity_extractor.resources)
        self.human = f"{self.pkg}.human_prompt_templates"
        self.human_prompts_files = {
            "chemical": "chemical_human_prompt.txt",
            "material": "material_human_prompt.txt",
        }

        # loading examples
        self.chemical_example = import_string_resource(
            self.examples, self.examples_files["chemical"]
        )
        self.material_example = import_string_resource(
            self.examples, self.examples_files["material"]
        )

        # loading system prompts
        self.material_system_prompt = import_string_resource(
            self.system, self.system_prompts_files["material"]
        )

        # loading human prompts
        self.material_human_prompt = import_string_resource(
            self.human, self.human_prompts_files["material"]
        )
        self.chemical_human_prompt = import_string_resource(
            self.human, self.human_prompts_files["chemical"]
        )

    blob_storage_base_url = "https://vdevdatastorage.blob.core.windows.net"
    keyword_analysis_blob = {
        "container": "keywords-analysis-container",
        "base_path": "keyword_analysis_results/documents",
    }
    keyword_analysis_blob = DotAccessDict(keyword_analysis_blob)

    customer_blob = {
        "container": "customer_blob_container",
        "base_path": "customer_blob_results/documents",
    }
    customer_blob = DotAccessDict(customer_blob)

    global_blob = {
        "container": "global_blob_container",
        "base_path": "global_blob_results/documents",
    }
    global_blob = DotAccessDict(global_blob)

    text_splitter_breakpoint_threshold_amount = 1.5
    text_splitter_breakpoint_threshold_type = "interquartile"

    # Example usage
    material_data = {
        "material_name": "Name of material",
        "material_no": "Number of material",
        "manufacturer_name": "Manufacturer's Name",
        "manufacturer_address": "Manufacturer's Address",
        "manufacturer_city": "Manufacturer's City",
        "manufacturer_postal_code": "Manufacturer's Postal Code",
        "manufacturer_country": "Manufacturer's Country",
        "manufacturer_state": "Manufacturer's State",
        "manufacturer_region": "Manufacturer's Region",
        "cas_no": "CAS Number of material",
        "ec_no": "EC Number of chemical",
        "chemicals": [
            {
                "chemical_name": "Name of chemical",
                "tag": "[Tag]",
                "cas_no": "CAS Number of chemical",
                "composition": "Chemical composition of chemical",
                "ec_no": "EC Number of chemical"
            },
            {
                "chemical_name": "Name of chemical",
                "tag": "[Tag]",
                "cas_no": "CAS Number of chemical",
                "composition": "Chemical composition of chemical",
                "ec_no": "EC Number of chemical"
            }
        ]
    }
    # llm_instance invocation

    example = {
        "material_data": {
            "material_name": "Silicon",
            "material_no": "SLS4102, SLS3313",
            "manufacturer_name": "ScienceLab.com Inc.",
            "manufacturer_address": "14025 Smith Rd",
            "manufacturer_city": "Houston",
            "manufacturer_postal_code": "77396",
            "manufacturer_country": "USA",
            "manufacturer_state": "Texas",
            "manufacturer_region": "Not available",
            "cas_no": "7440-21-3",
            "ec_no": "Not available",
            "chemicals": [
                {
                    "chemical_name": "Silicon",
                    "tag": "Primary",
                    "cas_no": "7440-21-3",
                    "composition": "100%",
                    "ec_no": "Not available"
                }
            ]
        }
    }

    # SYSTEM PROMPT TEMPLATE
    template = """
        Context: You will receive selected chunks from a safety datasheet of a material. Your task is to find the requested information based solely on the provided context. Use the following guidelines:

        1. Information Extraction:
           - For material_info, use only the given context to generate answers.
           - If any information is not in English, translate it and return the translated version.  
           - In the identification structure, extract name, address, contact, and emergency contact. Do not leave any fields blank, provide an appropriate message if any information is missing.
           - If the created on date is not mentioned in the MSDS, print an appropriate message. Do not leave the field blank.

        2. Format:
           - Return the answer in JSON format.

        Expected Output: {example}

        Note: Ensure accuracy and conciseness in the extracted information.
        """

    # HUMAN QUERY
    human_query = "context: {docs}, query: {query}"

    material_prompt = "Return material identification information and last date of revision. Check section 1."
    chemical_composition_prompt = "Return the chemical composition/Ingredients of the material provided. Check section 3 or 2."
