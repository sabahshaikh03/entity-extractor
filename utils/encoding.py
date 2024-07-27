import base64


class Encoding:
    def __init__(self, global_constants):
        self.global_constants = global_constants

    def encode_data(self, data):
        base64_encoded_file_uri = base64.b64encode(
            bytes(data, self.global_constants.utf_8)
        ).decode(self.global_constants.utf_8)
        return base64_encoded_file_uri
