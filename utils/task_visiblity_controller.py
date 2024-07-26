import threading
from utils.azure_queue import AzureQueue
from utils.threading_tools import ThreadingTool
import time
import pytz
from datetime import timedelta, datetime
from global_constants import GlobalConstants
from azure.storage.queue import QueueMessage

global_constants = GlobalConstants
azure_queue_util = AzureQueue()

_thread_local_queue_item = threading.local()


class TaskVisibilityController:
    @staticmethod
    def set_queue_item(queue_item):
        _thread_local_queue_item.data = {
            "queue_item": queue_item,
            "start_time": time.perf_counter(),
        }

    @staticmethod
    def clear_data():
        _thread_local_queue_item.data = {}

    @staticmethod
    def get_queue_item() -> QueueMessage:
        return _thread_local_queue_item.data.get("queue_item", (None, None))

    @classmethod
    def check_and_extend_visibility_timeout(cls) -> QueueMessage:
        queue_item = TaskVisibilityController.get_queue_item()
        if queue_item:
            start_time = cls.__get_start_time()

            extension_needed, elapsed_time = cls.__check_visible_on_threshold(
                queue_item.id, start_time
            )
            if extension_needed:
                queue_item = cls.__extend_visibility_timeout(elapsed_time, queue_item)

            return queue_item

    @classmethod
    def __get_start_time(cls):
        return _thread_local_queue_item.data.get("start_time", (None, None))

    @classmethod
    def __update_queue_item(cls, queue_item):
        _thread_local_queue_item.data["queue_item"] = queue_item

    @classmethod
    def __check_visible_on_threshold(cls, queue_item, start_time):
        current_time = datetime.now(pytz.utc)
        safe_visible_on_threshold = current_time + timedelta(
            seconds=global_constants.queue_visiblity_time * 0.1
        )
        next_visible_on = queue_item.next_visible_on.astimezone(pytz.utc)
        return (
            next_visible_on <= safe_visible_on_threshold,
            time.perf_counter() - start_time,
        )

    @classmethod
    def __extend_visibility_timeout(cls, elapsed_time, queue_item) -> QueueMessage:
        new_visibility_timeout = elapsed_time + int(
            global_constants.queue_visiblity_time
        )
        updated_queue_item = azure_queue_util.update_queue_message(
            message_id=queue_item.id,
            pop_receipt=queue_item.pop_receipt,
            visibility_timeout=new_visibility_timeout,
        )
        cls.__update_queue_item(queue_item)
        return updated_queue_item
