from global_constants import GlobalConstants
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from utils.encoding import Encoding
from msgraph.generated.shares.item.drive_item.drive_item_request_builder import (
    DriveItemRequestBuilder,
)
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.shares.shares_request_builder import SharesRequestBuilder
from msgraph import GraphServiceClient

global_constants = GlobalConstants

memo = {}


class SharePoint:
    def __init__(self, share_point_client: GraphServiceClient):
        self.share_point_client = share_point_client
        self.encoder = Encoding()

    async def read_file_from_share_point(self, file_uri):
        encoded_url = self.encode_url(file_uri)
        file_content = await self.share_point_client.shares.by_shared_drive_item_id(
            encoded_url
        ).drive_item.content.get()

        return file_content

    async def get_file_properties(self, file_uri):
        encoded_url = self.encode_url(file_uri)
        drive_item = await self.share_point_client.shares.by_shared_drive_item_id(
            encoded_url
        ).drive_item.get()

        return drive_item

    async def get_all_files_from_folder(self, folder_uri):
        file_locations = []
        next_link = folder_uri

        while next_link:
            encoded_uri = self.encode_url(next_link)

            # Get drive items by shared URL or drive URL
            if next_link == folder_uri:
                query_params = (
                    DriveItemRequestBuilder.DriveItemRequestBuilderGetQueryParameters(
                        expand=["children"]
                    )
                )
                request_configuration = RequestConfiguration(
                    query_parameters=query_params
                )
                result = await self.share_point_client.shares.by_shared_drive_item_id(
                    encoded_uri
                ).drive_item.get(request_configuration=request_configuration)
            else:
                query_params = (
                    SharesRequestBuilder.SharesRequestBuilderGetQueryParameters(
                        expand=["children"]
                    )
                )
                request_configuration = RequestConfiguration(
                    query_parameters=query_params
                )
                result = await self.share_point_client.shares.with_url(next_link).get(
                    request_configuration=request_configuration
                )

            # Process the result
            for child in result.children if next_link == folder_uri else result.value:
                if getattr(child, "folder", None):
                    nested_files = await self.get_files_from_folder(child.web_url)
                    file_locations.extend(nested_files)
                else:
                    file_locations.append(child.web_url)

            # Check if there are more pages to fetch
            next_link = result.additional_data.get("children@odata.nextLink")

        return file_locations

    def is_drive_item_folder(self, item):
        return getattr(item, "folder", None) or (
            hasattr(item, "additional_data") and "folder" in item.additional_data
        )

    async def fetch_drive_items(self, shared_url=None, page_link=None):
        if shared_url:
            encoded_uri = self.encode_url(shared_url)
            query_params = (
                DriveItemRequestBuilder.DriveItemRequestBuilderGetQueryParameters(
                    expand=["children"]
                )
            )
            request_configuration = RequestConfiguration(query_parameters=query_params)
            result = await self.share_point_client.shares.by_shared_drive_item_id(
                encoded_uri
            ).drive_item.get(request_configuration=request_configuration)

        if page_link:
            query_params = SharesRequestBuilder.SharesRequestBuilderGetQueryParameters(
                expand=["children"]
            )
            request_configuration = RequestConfiguration(query_parameters=query_params)
            result = await self.share_point_client.shares.with_url(page_link).get(
                request_configuration=request_configuration
            )

        # Check if there are more pages to fetch
        next_page_link = result.additional_data.get("children@odata.nextLink")

        result = result.children if shared_url else result.value
        return result, next_page_link

    async def get_files_from_folder_in_batch(
        self,
        root_folder_uri=None,
        page_link=None,
        batch_size=10,
    ):
        file_locations = []

        # Fetch drive items from sharepoint
        result, next_page_link = await self.fetch_drive_items(
            root_folder_uri, page_link
        )

        # Process the result
        for child in result:
            if self.is_drive_item_folder(child):
                nested_files, next_link = await self.get_files_from_folder_in_batch(
                    root_folder_uri=child.web_url, next_page_link=next_page_link
                )
                file_locations.extend(nested_files)
            else:
                file_locations.append(child.web_url)

        return (file_locations, next_page_link)

    def encode_url(self, file_uri):
        base64_value = self.encoder.encode_data(file_uri)
        encoded_url = (
            f"{global_constants.u}{global_constants.symbols.exclamatory_mark}"
            + base64_value.replace(
                global_constants.symbols.equal_to, global_constants.symbols.empty_string
            )
            .replace(
                global_constants.symbols.forward_slash,
                global_constants.symbols.underscore,
            )
            .replace(global_constants.symbols.plus, global_constants.symbols.minus)
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
