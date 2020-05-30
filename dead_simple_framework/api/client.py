# Requests
import requests

# API Utilities
from .utils import create_query_string

# API Errors
from .errors import API_Client_Error

# Utilities
from time import sleep


class API:
    ''' Client for making HTTP requests  '''

    @staticmethod
    def get(url:str, query_params:dict=None, ignore_errors=False, retry_ms=500, num_retries=3):
        ''' [HTTP GET] Fetch a resource from an API '''

        # Format URL to send the request to
        url = f"{url}{create_query_string(query_params)}"

        for x in range(0, num_retries):
            # Send the request
            result = requests.get(url, headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
                "Cache-Control": "no-cache"
            })

            # Check for errors
            if result.status_code != 200:
                if not ignore_errors:
                    raise API_Client_Error(url, 'GET', result.status_code)
                else:
                    return None

            # Check for actual result
            if result.text:
                return result

            # Otherwise wait, then rety
            sleep(retry_ms/1000)

        return result if result.text else None


    @staticmethod
    def get_json(url:str, query_params:dict=None, ignore_errors=False, retry_ms=500, num_retries=3) -> dict:
        ''' [HTTP GET] Fetch a JSON from an API '''

        # Get the raw result
        res = API.get(url, query_params, ignore_errors, retry_ms, num_retries)

        # Extract data into dictionary
        return res.json() if res else {}
