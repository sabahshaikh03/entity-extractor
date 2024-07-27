import os
import dotenv

dotenv.load_dotenv()


class DotAccessDict(dict):
    def __getattr__(self, attr):
        if attr in self:
            return self[attr]
        else:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{attr}'"
            )


class EntityExtractorConstants(DotAccessDict):
    # Environment Variables
    embedding_deployment = os.getenv("EMBEDDING_DEPLOYMENT")
    llm_deployment = os.getenv("LLM_DEPLOYMENT")
    azure_openai_endpoint = os.getenv("ENDPOINT")
    openai_api_version = os.getenv("OPENAI_API_VERSION")
    azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_app_insights_connector = os.getenv("APPINSIGHTS_CONNECTION_STRING")
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_auth = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))

    pg_host = os.getenv("PgVectorHost")
    pg_port = os.getenv("PgVectorPort")
    pg_user = os.getenv("PgVectorUsername")
    pg_password = os.getenv("PgVectorPassword")
    pg_dbname = os.getenv("PgVectorDatabase")

    # Output Example
    example = {
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

    # Labels for Named Entity Recognition using GLiNER
    labels = [
        "Material Name",
        "Manufacturer Name",
        "Manufacturer Address",
        "Manufacturer Contact",
        "Created By",
        "Creation Date",
        "Revision Date",
        "Chemical Name",
        "Chemical Other Information",
        "CAS Number",
        "Concentration",
    ]

    # Prompts
    template = """
    Context: You will receive selected chunks from a safety datasheet of a material. Your task is to find the requested information based solely on the provided context. Use the following guidelines:

    1. Information Extraction:
       - For material_info, use only the given context to generate answers.
       - For chemical_level_toxicity, if specific information for that chemical is not available in the document provided, look up information about that chemical and generate an appropriate answer.
       - For fields related to toxicity, if information is not available in the context, answer the query by referring to external knowledge.
       - If any information is not in English, translate it and return the translated version.  
       - In the identification structure, extract name, address, contact, and emergency contact. Do not leave any fields blank; provide an appropriate message if any information is missing.
       - If the created on date is not mentioned in the MSDS, print an appropriate message. Do not leave the field blank.

    2. Format:
       - Return the answer in JSON format.

    Expected Output: {example}

    Note: Ensure accuracy and conciseness in the extracted information.
    """

    old_prompt = """
    As a highly skilled chemist specializing in per- and polyfluoroalkyl substances (PFAS) detection, your task is to analyze Material Safety Data Sheets (MSDS) to identify the presence of PFAS in various materials. Your expertise lies in extracting and assessing the chemical composition of each listed component within the material, including the Manufacturer's Name. Your role also involves utilizing your knowledge of PFAS chemistry and regulations to compare identified chemical structures and synonyms against established PFAS databases. You are to classify each component using specific tags denoting its PFAS status: "PFAS": Indicates the presence of one or more identified PFAS chemicals. "Potential PFAS": Suggests the presence of structures or synonyms indicative of PFAS, requiring further investigation for confirmation. "NO_PFAS": Signifies the absence of any known PFAS within the component. Your output should be in pure JSON format, following the specified structure: {"material_name":"Name of material","material_no":"Number of material","manufacturer_name":"Manufacturer's Name","manufacturer_address":"Manufacturer's Address","manufacturer_city":"Manufacturer's City","manufacturer_postal_code":"Manufacturer's Postal Code","manufacturer_country":"Manufacturer's Country","manufacturer_state":"Manufacturer's State","manufacturer_region":"Manufacturer's Region","cas_no":"CAS Number of material","ec_no":"EC Number of chemical","chemicals":[{"chemical_name":"Name of chemical","tag":"[Tag]","cas_no":"CAS Number of chemical","composition":"Chemical composition of chemical","ec_no":"EC Number of chemical"},{"chemical_name":"Name of chemical","tag":"[Tag]","cas_no":"CAS Number of chemical","composition":"Chemical composition of chemical","ec_no":"EC Number of chemical"}]} Please note: Do not provide any other information beyond the requested format. Provide the information in JSON format and keys should be fixed as mentioned above. Content: CONTENT
    """

    human_query = "context: {docs}, query: {query}"

    order = [
        "document_name",
        "identification",
        "material_composition",
        "total_tokens",
        "total_cost"
    ]

    # prompts
    identification_prompt = "Return material identification information and last date of revision. Check section 1."
    chemical_composition_prompt = "Return the chemical composition/Ingredients of the material provided. Check section 3 or 2."
    toxicological_info_prompt = "Return toxicological information. Check section 11."

    # chunking parameters

    # semantic
    text_splitter_breakpoint_threshold_type = "interquartile"
    text_splitter_breakpoint_threshold_amount = 1.5

    # recursive chunking parameters
    chunk_size = 2000
    overlap = 200

    # fast tokenizer
    chunk_token_limit = 3072
