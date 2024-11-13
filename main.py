import json
import re
from datetime import datetime
from typing import Dict, List

from apis import fetch_jobs_from_board
from parse import filter_jobs, standardize_jobs
from rss import convert_to_rss
from syndication_types import ApiDefinition, BoardConfig


def get_board_name_from_uri(api_url: str) -> str:
  board_pattern = re.compile(r"boards/([^/]+)/")
  board_match = board_pattern.search(api_url)
  return board_match.group(1) if board_match else None


def main():
  try:
    with open("api_definitions.json", "r") as f:
      api_definitions: Dict[str, ApiDefinition] = json.load(f)
  except FileNotFoundError:
    print(
        "Error: api_definitions.json not found. Please ensure this file exists in the current directory."
    )
    return

  try:
    with open("boards.json", "r") as f:
      apis: List[BoardConfig] = json.load(f)
  except FileNotFoundError:
    print(
        "Error: boards.json not found. Please ensure this file exists in the current directory."
    )
    return

  try:
    with open("criteria.json", "r") as f:
      criteria: Dict = json.load(f)
  except FileNotFoundError:
    print(
        "Error: boards.json not found. Please ensure this file exists in the current directory."
    )
    return

  # Fetch jobs from all APIs
  all_jobs = []
  for api in apis:
    board_name = get_board_name_from_uri(api["board_uri"])
    print(f"----Board name: {board_name}-----")
    adapter = api_definitions[api["adapter"]]
    uri = api["board_uri"]
    jobs = fetch_jobs_from_board(uri, adapter)
    standarized_jobs = standardize_jobs(jobs, adapter, api["company_name"])
    (filtered_jobs, filter_stats) = filter_jobs(standarized_jobs, criteria)
    print(filter_stats)
    all_jobs.extend(filtered_jobs)
  rss_feed = convert_to_rss(all_jobs)
  # Write RSS feed to file
  with open("jobs.rss", "w") as f:
    f.write(rss_feed)


if __name__ == "__main__":
  main()
