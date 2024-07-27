from utils.dot_access_dict import DotAccessDict
from utils.import_resources import import_string_resource


class AskViridiumConstants:
    def __init__(self):
        super().__init__()
        self.pkg = "app.modules.ask_viridium_ai.resources"

        # creating root directory reference for examples (app.modules.ask_viridium_ai.resources.examples)
        self.examples = f"{self.pkg}.examples"
        self.examples_files = {
            "chemicals": "find_chemicals_example.json",
            "analysis": "material_analysis_example.json",
        }

        # creating root directory reference for system prompt templates (app.modules.ask_viridium_ai.resources.examples)
        self.system = f"{self.pkg}.system_prompt_templates"
        self.system_prompts_files = {
            "chemicals": "find_chemicals_system_prompt.txt",
            "analysis": "material_analysis_system_prompt.txt",
        }

        # creating root directory reference for human prompt templates (app.modules.ask_viridium_ai.resources.examples)
        self.human = f"{self.pkg}.human_prompt_templates"
        self.human_prompts_files = {
            "chemicals": "find_chemicals_human_prompt.txt",
            "analysis": "material_analysis_human_prompt.txt",
        }

        # loading examples
        self.chemical_composition_example = import_string_resource(
            self.examples, self.examples_files["chemicals"]
        )
        self.material_analysis_example = import_string_resource(
            self.examples, self.examples_files["analysis"]
        )

        # loading system prompts
        self.material_composition_system_prompt = import_string_resource(
            self.system, self.system_prompts_files["chemicals"]
        )
        self.material_analysis_system_prompt = import_string_resource(
            self.system, self.system_prompts_files["analysis"]
        )

        # loading human prompts
        self.material_composition_human_prompt = import_string_resource(
            self.human, self.human_prompts_files["chemicals"]
        )
        self.material_analysis_human_prompt = import_string_resource(
            self.human, self.human_prompts_files["analysis"]
        )

        # AzureChatOpenAI params for AskVAI
        self.temperature = 0
        self.max_tokens = 800
        self.timeout = 60


class AskViridiumInputParameters(DotAccessDict):
    def __init__(self):
        super().__init__()
        self.input_parameters = {
            "material_name": "material_name",
            "manufacturer_name": "manufacturer_name",
        }
        self.input_parameters = DotAccessDict(self.input_parameters)
