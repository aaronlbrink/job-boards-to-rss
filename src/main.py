import json
from datetime import datetime
from typing import Dict, List

from src.apis import fetch_data_from_board
from src.parse import parse_jobs
from src.rss import convert_to_rss
from src.types import ApiDefinition, BoardConfig


def hydrate_api_definition(api_definition: ApiDefinition,
                           api_vars: Dict) -> ApiDefinition:
  hydrated_definition = json.loads(json.dumps(api_definition))

  if "vars" not in hydrated_definition:
    return hydrated_definition

  vars_to_replace = hydrated_definition["vars"]
  definition_str = json.dumps(hydrated_definition)

  for var_name, var_placeholder in vars_to_replace.items():
    if var_name in api_vars:
      definition_str = definition_str.replace(
          var_placeholder, api_vars[var_name])

  return json.loads(definition_str)


def main():
  try:
    with open("src/api_definitions.json", "r") as f:
      api_definitions: Dict[str, ApiDefinition] = json.load(f)
  except FileNotFoundError:
    print(
        "Error: api_definitions.json not found. Please ensure this file exists in the current directory."
    )
    return

  try:
    with open("src/boards.json", "r") as f:
      apis: List[BoardConfig] = json.load(f)
  except FileNotFoundError:
    print(
        "Error: boards.json not found. Please ensure this file exists in the current directory."
    )
    return

  try:
    with open("src/criteria.json", "r") as f:
      criteria: Dict = json.load(f)
  except FileNotFoundError:
    print(
        "Error: boards.json not found. Please ensure this file exists in the current directory."
    )
    return

  # Fetch jobs from all APIs
  all_jobs = []
  failed_jobs = []
  for api in apis:
    print(f"----Board name: {api['company_name']}-----")
    adapter = api_definitions[api["adapter"]]
    api_def = None
    if 'api_vars' in api:
      api_def = hydrate_api_definition(adapter, api['api_vars'])
    else:
      api_def = adapter
    data = fetch_data_from_board(api["board_uri"], api_def)
    jobs = parse_jobs(data, api_def, api["company_name"], criteria)
    all_jobs.extend(jobs["passed"])
    failed_jobs.extend(jobs["failed"])
  print(f"Total jobs sent to RSS: {len(all_jobs)}")
  rss_feed = convert_to_rss(all_jobs)

  if True:
    with open("debug.json", "w") as f:
      json.dump(failed_jobs, f, indent=2, default=str)
  # Write RSS feed to file
  with open("jobs.rss", "w") as f:
    f.write(rss_feed)


if __name__ == "__main__":
  main()
