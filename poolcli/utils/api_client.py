from typing import Any, Optional

import requests

from poolcli.utils.console import console
from poolcli.utils.error_handler import handle_error
from poolcli.utils.misc import get_auth_headers


class APIClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def create_request(
        self,
        path: str,
        method: str = "GET",
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        timeout: int = 20,
        verify: bool = True,
        token: Optional[str] = None,
    ) -> dict[Any, Any]:
        """
        Creates a generalized HTTP request using the requests library.

        Args:
            url (str): The URL to send the request to
            method (str, optional): HTTP method (GET, POST, PUT, DELETE, etc). Defaults to "GET".
            params (Dict, optional): URL parameters to include in the request. Defaults to None.
            headers (Dict, optional): HTTP headers to include in the request. Defaults to None.
            json_data (Dict, optional): JSON data to send in the request body. Defaults to None.
            timeout (int, optional): Request timeout in seconds. Defaults to 30.
            verify (bool, optional): Whether to verify SSL certificates. Defaults to True.

        Returns:
            requests.Response: Response object from the request

        Raises:
            requests.exceptions.RequestException: For any request-related errors
        """
        method = method.upper()
        headers = get_auth_headers(token)
        url = f"{self.base_url.lstrip('/')}/{path.rstrip('/')}"

        request_kwargs = {"url": url, "headers": headers, "params": params, "timeout": timeout, "verify": verify}

        if method in ["POST", "PUT", "PATCH"]:
            if json_data is not None:
                request_kwargs["json"] = json_data

        try:
            with console.status(f"[bold green]Making {method} request to {url}...", spinner="earth"):
                response = requests.request(method, **request_kwargs)
                data = response.json()
                handle_error(data=data, response=response)
            return data
        except requests.exceptions.RequestException:
            raise
