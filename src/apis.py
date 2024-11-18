import json
from typing import Dict, List

import requests

from src.parse import get_json_key
from src.types import ApiDefinition


def get_paginated_response_json(api_definition: ApiDefinition, request_method: str, url: str,
                                request_headers: Dict = None, request_body: Dict = None) -> List[Dict]:
  response_jsons = {}
  pagination_config = api_definition["pagination"]
  limit_field_name = pagination_config["limit_field"]
  offset_field_name = pagination_config["offset_field"]
  remaining_field_name = pagination_config["remaining"]
  root_field_name = api_definition["response"]["root"]

  request_body[limit_field_name] = pagination_config["limit_value"]
  request_body[offset_field_name] = pagination_config["offset_value"]

  # Create key for results
  parts = root_field_name.split(".")
  for i, part in enumerate(parts):
    if i == len(parts) - 1:
      response_jsons[part] = []
    else:
      response_jsons[part] = {}

  total_results = 1
  offset = pagination_config["offset_value"]
  while int(offset) < int(total_results):
    # print(f"Offset: {offset}; Total results: {total_results}")
    response_json = get_response_json(
        request_method, url, request_headers, request_body)
    jobs = get_json_key(response_json, root_field_name)
    hook = get_json_key(response_jsons, root_field_name)
    hook.extend(jobs)

    total_results = response_json[remaining_field_name]
    offset = int(
        request_body[offset_field_name]) + int(pagination_config["limit_value"])
    request_body[offset_field_name] = offset

  return response_jsons


def get_response_json(method: str, url: str,
                      headers: Dict = None, body: Dict = None) -> List[Dict]:
  try:
    # print(method, url, headers, body)
    response = requests.request(method, url, headers=headers, json=body)
    response.raise_for_status()
    return response.json()
  except Exception as e:
    print(f"Error fetching jobs from {url}: {str(e)}")


def fetch_data_from_board(
        url: str, api_definition: ApiDefinition) -> List[Dict]:
  request_config = api_definition["request"]
  request_method = request_config["type"]
  request_headers = request_config["headers"] if "headers" in request_config else None
  request_body = request_config["body"]["content"] if "body" in request_config else None

  if "pagination" in api_definition:
    response_json = get_paginated_response_json(
        api_definition, request_method, url, request_headers, request_body)
  else:
    response_json = get_response_json(
        request_method, url, request_headers, request_body)
  return response_json
