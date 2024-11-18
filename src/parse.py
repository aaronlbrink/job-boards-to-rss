import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

# from fixed_data import cities, counties, state_ids, states
from src.parse_stats import ParseJobsStats
from src.types import ApiDefinition


# Takes in json, like: {"location": [{"state": "Alaska"}, {"state": "Alabama"}]}
# and returns: ["Alaska", "Alabama"]
def flatten_json_to_list(obj) -> str:
  result = []
  # Warning: Recursive. (TODO) Reimplemnt without recursion

  def _flatten(current_obj, current_path=""):
    if isinstance(current_obj, dict):
      for key, value in current_obj.items():
        _flatten(value, f"{current_path}.{key}" if current_path else key)
    elif isinstance(current_obj, list):
      for i, item in enumerate(current_obj):
        _flatten(item, f"{current_path}[{i}]")
    else:
      result.append(str(current_obj).replace(',', '').strip())

  _flatten(obj)
  return " ".join(result)


# Question: Does this only work for json?
# TODO: Add documentation for this function (give examples how it works)
def get_json_key(obj: any, path: str) -> any:
  for part in path.split("."):
    if isinstance(obj, dict) and part in obj:
      obj = obj[part]
    else:
      raise ValueError(f"Key not found: {part}")
  return obj


def find_years_of_experience_in_job(job_json_str: str) -> int | None:
  experience_patterns = [
      # Handles "10+ years experience" - this pattern needs to be first
      r"(\d+)\+\s*(?:years|yrs)",
      # Handles ">5 years" or "≥5 years"
      r"[>≥](\d+)\+?\s*(?:years|yrs)",
      # Handles "minimum of 5 years"
      r"minimum\s*(?:of\s*)?(\d+)(?:\s*-\s*\d+)?\+?\s*(?:years|yrs)",
      # Handles "at least 5 years"
      r"at\s*least\s*(\d+)(?:\s*-\s*\d+)?\+?\s*(?:years?|yrs?)",
      # Handles "5-10 years experience"
      r"(\d+)(?:\s*-\s*\d+)?\s*(?:years|yrs)(?:\s*of)?\s*(?:experience|exp)",
      # Handles "5 years" or "5-10 years"
      r"(\d+)(?:\s*-\s*\d+)?\s*(?:years|yrs)",
      # Handles written numbers like "three years"
      r"(one|two|three|four|five|six|seven|eight|nine)\s*(?:years?|yrs?)(?:\s*of)?\s*(?:experience|exp)?",
  ]
  number_map = {
      'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
      'six': 6, 'seven': 7, 'eight': 8, 'nine': 9
  }

  for pattern in experience_patterns:
    matches = re.findall(pattern, job_json_str)
    for match in matches:
      try:

        if isinstance(match, str) and match.lower() in number_map:
          return number_map[match.lower()]
        years = int(match.split("-")[0].strip())
        return years
      except ValueError:
        continue


def location_match(locations: str, criteria: Dict) -> bool:
  if not locations or not criteria["location_whitelist"]:
    return False
  criteria_locations = [cased.lower()
                        for cased in criteria["location_whitelist"]]
  # locations_str = " ".join(locations).lower()
  return bool(re.search(
      f"({'|'.join(re.escape(loc) for loc in criteria_locations)})", locations.lower()))


def role_match(title: str, description: str, criteria: Dict) -> List[str]:
  # print("role match", title, description, criteria["role_terms"])
  found_roles = set([])
  title_and_description = title.lower() + " " + description.lower()
  # TODO: This runs slow
  found_roles.update(
      role for role in criteria["role_terms"] if role.lower() in title_and_description)
  return list(found_roles)


# def parse_location(location: str | List[Dict]) -> str:
#   if isinstance(location, list):
#     location_string = ""
#     for place in location:
#       location_string += f"{place.get('city', '') or ''} {place.get('town', '') or ''} {place.get('country', '') or ''} {place.get('region', '') or ''} {place.get('postal_code', '') or ''}, ".strip()
#     return location_string.rstrip(", ")
#   return location

def find_cities_in_json_str(job_json_str: str, criteria: Dict) -> str:
  cities_pattern = r"\b(" + "|".join(re.escape(city.lower())
                                     for city in criteria["location_whitelist"]) + r")\b"
  compiled_pattern = re.compile(cities_pattern)

  matches = compiled_pattern.findall(job_json_str.lower())

  return " ".join(set(matches))


def parse_jobs(data: List[Dict], api_definition: ApiDefinition,
               company_name: str, criteria: Dict) -> List[Dict]:
  stats = ParseJobsStats()
  response_config = api_definition["response"]
  root = response_config["root"]
  job_format = response_config["job_format"]
  parsed_jobs = []
  excluded_jobs = []
  all_jobs = get_json_key(data, root)
  stats.total = len(all_jobs)

  for job in all_jobs:
    filter_failures = []
    #
    # Filters jobs by:
    #   (1) using rule-based filters (ie. does location match our criteria filters?),
    #   (2) (TODO) Asking an LLM if it should be included
    # (TODO) Then, formats jobs by: (TODO) Using an LLM to output structured data
    #
    matching_criteria = {
        "location": False,
        "years_of_experience": False,
        "role": False,
        "no_title_blacklist_words": True,


    }
    nice_job = {k: get_json_key(job, v)
                for k, v in job_format.items()}

    nice_job["json_str"] = json.dumps(job)

    # Apply City Rules
    #
    nice_job["location"] = flatten_json_to_list(nice_job["location"])
    matching_criteria["location"] = location_match(
        nice_job["location"], criteria)
    if matching_criteria["location"]:
      stats.location_success_count += 1
      # Won't have to do slow search in job post since we have a match here
    else:
      nice_job["location"] = find_cities_in_json_str(
          nice_job["json_str"], criteria)
      matching_criteria["location"] = location_match(
          nice_job["location"], criteria)
      if matching_criteria["location"]:
        stats.location_success_count += 1
      else:
        filter_failures.append("zero location matches anywhere in job")

    nice_job["company"] = company_name

    if nice_job.get("created_at"):
      try:
        nice_job["created_at"] = datetime.strptime(
            nice_job["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
        ).isoformat()
        # print("made iso date!")
      except ValueError:
        nice_job["created_at"] = datetime.now().isoformat()
    else:
      # TODO: Don't just set to now!
      nice_job["created_at"] = datetime.now().isoformat()

    # _____REMOVE LINE_____

    # Role check
    title = nice_job.get("title", "")
    description = nice_job.get("description", "")
    nice_job["role"] = role_match(title, description, criteria)
    if len(nice_job["role"]) > 0:
      stats.role_success_count += 1
      matching_criteria["role"] = True
    else:
      stats.role_failure_count += 1
      filter_failures.append("No matching title found anywhere in job")

    # Custom filters
    # job_dump = json.dumps(nice_job)
    # TODO: Why does this not seem to work?

    for word in title.split(" "):
      if word.lower() in [
              term.lower()
              for term in criteria["title_blacklist"]] and word.strip():
        # print(f"Excluding {title} because of word in custom filter: {word}")
        stats.custom_filter_failure_count += 1
        matching_criteria["no_title_blacklist_words"] = False
        filter_failures.append("A blacklisted word was found in the title")

    # Years of experience check
    nice_job["years_of_experience"] = find_years_of_experience_in_job(
        nice_job["json_str"])
    if not nice_job["years_of_experience"] or not isinstance(
            nice_job["years_of_experience"], int):
      stats.unspecified_years_of_experience_failure_count += 1
      filter_failures.append(
          "Number of years of experience required not known/not found")
    elif nice_job["years_of_experience"] > criteria["max_years_of_experience"]:
      stats.not_enough_years_of_experience_failure_count += 1
      filter_failures.append("Years of experience is higher than my critera")
    else:
      stats.years_of_experience_success_count += 1
      matching_criteria["years_of_experience"] = True

    if all(matching_criteria.values()):
      parsed_jobs.append(nice_job)
    else:
      nice_job["failed_reason"] = " ".join(filter_failures)
      excluded_jobs.append(nice_job)

  stats.passed_all_filters = len(parsed_jobs)
  stats.print_stats()

  return {"passed": parsed_jobs, "failed": excluded_jobs}
