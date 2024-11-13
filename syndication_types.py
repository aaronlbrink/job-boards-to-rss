from typing import Dict, TypedDict


class BoardConfig(TypedDict):
  adapter: str
  board_uri: str


class JobFormatDefinition(TypedDict):
  title: str
  url: str
  description: str
  location: str
  created_at: str
  updated_at: str


class RequestDefinition(TypedDict):
  type: str
  headers: Dict[str, str]
  body: Dict[str, any]


class ResponseDefinition(TypedDict):
  root: str
  job_format: JobFormatDefinition


class ApiDefinition(TypedDict):
  request: RequestDefinition
  response: ResponseDefinition
