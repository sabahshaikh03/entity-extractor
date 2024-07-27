from flask import jsonify, Response
from typing import Any


def return_api_response(
    status, message, logger, constants, result=None, additional_data=None
) -> tuple[Response, Any]:
    """
    Constructs and returns a JSON response.

    Args:
        status (int): The status code of the response.
        message (str): The message of the response.
        result (Any, optional): The result of the response. Defaults to None.
        additional_data (dict, optional): Additional data to include in the response. Defaults to None.
        constants: global constants for api response status codes
        logger: global logger

    Returns:
        tuple: A tuple containing the JSON response and the status code.
    """

    response_data = {
        constants.api_response_parameters.status: status,
        constants.api_response_parameters.message: message,
        constants.api_response_parameters.result: result,
    }
    if additional_data:
        response_data.update(additional_data)

    logger.info(f"Returning API response: {response_data}")
    return jsonify(response_data), status


def validate_request_data(request_data, required_params, logger):
    """
    Validates that all required parameters are present in the request data.

    Args:
        request_data (dict): The request data to validate.
        required_params (list): The list of required parameters.
        logger: global logger

    Returns:
        tuple: A tuple containing a boolean indicating if the validation was successful and a list of missing parameters if applicable.
    """
    missing_params = [param for param in required_params if param not in request_data]
    if missing_params:
        logger.warning(f"Validation failed. Missing parameters: {missing_params}")
        return missing_params
    return None
