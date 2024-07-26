import json
from connectors.azure_open_ai_connector import AzureOpenAIConnector
from connectors.key_vault_connector import AzureKeyVaultConnector
from global_constants import GlobalConstants
from logging import Logger

global_constants = GlobalConstants


class OpenAI:
    def __init__(self, logger: Logger):
        self.logger = logger
        kv_client = AzureKeyVaultConnector()
        self.client = AzureOpenAIConnector().connect()
        self.deployment = kv_client.get_secret(
            global_constants.keys_of_key_vault_secrets.azure_openai_deployment_name
        )

    def complete_chat_turbo(
        self, content: str = None, system_content: str = None
    ) -> str:

        messages = []
        if content:
            messages.append({"role": "user", "content": content})
        if system_content:
            messages.append({"role": "system", "content": system_content})

        completion = self.client.chat.completions.create(
            model=self.deployment,
            messages=messages,
            max_tokens=800,
            temperature=0.7,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=False,
        )

        response = json.loads(completion.to_json())
        return response["choices"][0]["message"]["content"]

    def get_embeddings(self, content: str) -> list:
        try:
            # Construct the input payload for the embeddings request
            embedding_request = {"model": self.deployment, "input": content}

            # Make the API call to retrieve embeddings
            embedding_response = self.client.embeddings.create(embedding_request)

            # Extract the embeddings from the response
            embeddings = json.loads(embedding_response.to_json())
            return embeddings["data"][0]["embedding"]

        except Exception as e:
            self.logger.error(f"Failed to get embeddings: {str(e)}")
            raise
