import base64
from global_constants import GlobalConstants


class Encoding:
    def __init__(self):
        self.global_constants = GlobalConstants

    def encode_data(self, data):
        base64_encoded_file_uri = base64.b64encode(
            bytes(data, self.global_constants.utf_8)
        ).decode(self.global_constants.utf_8)
        return base64_encoded_file_uri
