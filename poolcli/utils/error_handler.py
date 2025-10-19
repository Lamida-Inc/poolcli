import requests


def handle_error(response: requests.Response, data: dict):
    error_msg = ""
    if 400 <= response.status_code < 500 or 500 <= response.status_code < 600:
        error_msg = data["message"]
        raise Exception(error_msg)
