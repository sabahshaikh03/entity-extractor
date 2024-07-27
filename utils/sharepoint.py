from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from utils.encoding import Encoding


class SharePoint:
    def __init__(self, share_point_client, global_constants):
        self.global_constants = global_constants
        self.share_point_client = share_point_client
        self.encoder = Encoding(self.global_constants)

    async def read_file_from_share_point(self, file_uri):
        encoded_url = self.encode_url(file_uri)
        file_content = await self.share_point_client.shares.by_shared_drive_item_id(
            encoded_url
        ).drive_item.content.get()

        return file_content

    def encode_url(self, file_uri):
        base64_value = self.encoder.encode_data(file_uri)
        encoded_url = (
            f"{self.global_constants.u}{self.global_constants.symbols.exclamatory_mark}"
            + base64_value.replace(
                self.global_constants.symbols.equal_to,
                self.global_constants.symbols.empty_string,
            )
            .replace(
                self.global_constants.symbols.forward_slash,
                self.global_constants.symbols.underscore,
            )
            .replace(
                self.global_constants.symbols.plus, self.global_constants.symbols.minus
            )
        )
        return encoded_url

    async def check_if_file_exists(self, file_uri):
        try:
            encoded_url = self.encode_url(file_uri)
            await self.share_point_client.shares.by_shared_drive_item_id(
                encoded_url
            ).drive_item.get()
            return True
        except ODataError:
            return False
