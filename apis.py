from typing import Dict, List

import requests

from syndication_types import ApiDefinition


def get_response_json(method: str, url: str,
                      headers: Dict = None, body: Dict = None) -> List[Dict]:
  try:
    print(method, url, headers, body)
    response = requests.request(method, url, headers=headers, json=body)
    response.raise_for_status()
    return response.json()
  except Exception as e:
    print(f"Error fetching jobs from {url}: {str(e)}")


def fetch_jobs_from_board(
        url: str, api_definition: ApiDefinition) -> List[Dict]:
  request_config = api_definition["request"]
  request_method = request_config["type"]
  request_headers = request_config["headers"] if "headers" in request_config else None
  request_body = request_config["body"] if "body" in request_config else None
  response_json = get_response_json(
      request_method, url, request_headers, request_body)
  return response_json
