import json
from connectors.azure_queue_connector import AzureQueueConnector
from azure.core.exceptions import ResourceNotFoundError


class AzureQueue:
    def __init__(self, global_constants):
        self.global_constants = global_constants
        self.azure_queue_client = AzureQueueConnector(self.global_constants).connect()

    def enqueue(self, payload):
        self.azure_queue_client.send_message(json.dumps(payload))
        return True

    def dequeue(self, visiblity_timeout):
        return self.azure_queue_client.receive_message(
            visibility_timeout=visiblity_timeout
        )

    def delete_queue_item(self, queue_item):
        try:
            self.azure_queue_client.delete_message(queue_item)
            return True
        except ResourceNotFoundError:
            return False

    def get_queue_length(self):
        properties = self.azure_queue_client.get_queue_properties()
        count = properties.approximate_message_count
        return count

    def update_queue_message(
        self, message_id, pop_receipt, visibility_timeout=0, new_content=None
    ):
        updated_message = self.azure_queue_client.update_message(
            message_id,
            pop_receipt=pop_receipt,
            content=new_content,
            visibility_timeout=visibility_timeout,
        )
        return updated_message
