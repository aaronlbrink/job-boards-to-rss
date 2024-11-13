import json
import re
from datetime import datetime
from typing import Dict, List, Tuple

from syndication_types import ApiDefinition


# Question: Does this only work for json?
def get_json_key(obj: any, path: str) -> any:
  for part in path.split("."):
    if isinstance(obj, dict) and part in obj:
      obj = obj[part]
    else:
      raise ValueError(f"Key not found: {part}")
  return obj


def find_years_of_experience_in_job(job: Dict) -> int:
  content = job.get("description", "").lower()
  experience_patterns = [
      r"(\d+)(?:\s*-\s*\d+)?\+?\s*(?:years|yrs)(?:\s*of)?\s*(?:experience|exp)",
      r"minimum\s*(?:of\s*)?(\d+)(?:\s*-\s*\d+)?\+?\s*(?:years|yrs)",
      r"at\s*least\s*(\d+)(?:\s*-\s*\d+)?\+?\s*(?:years|yrs)",
      r"[>≥](\d+)\+?\s*(?:years|yrs)",
  ]

  for pattern in experience_patterns:
    matches = re.findall(pattern, content)
    for match in matches:
      try:
        # Take the first number in ranges like "2-5"
        # Handle both single numbers and ranges (e.g. "2" or "2-5")
        years = int(match.split("-")[0].strip())
        return years
      except ValueError:
        continue


def should_include_job(job: Dict, criteria: Dict) -> Dict[str, any] | bool:
  """
  Filters jobs based on location, role type, and years of experience.
  """
  # Location check
  location = job.get("location", "").lower()

  location_match = any(term in location for term in criteria["location_terms"])
  if not location_match:
    return {"exclude_reason": "location"}

  # Role check
  title = job.get("title", "").lower()
  description = job.get("description", "").lower()

  role_match = any(
      term in title or term in description for term in criteria["role_terms"])
  if not role_match:
    return {"exclude_reason": "role"}

  # Years of experience check
  years_of_experience = job.get("years_of_experience", None)
  if not years_of_experience:
    # return {"exclude_reason": "unspecified_years_of_experience"}
    return True
  if years_of_experience > criteria["max_years_of_experience"]:
    return {"exclude_reason": "years_of_experience"}

  return True


# def parse_location(location: str | List[Dict]) -> str:
#   if isinstance(location, list):
#     location_string = ""
#     for place in location:
#       location_string += f"{place.get('city', '') or ''} {place.get('town', '') or ''} {place.get('country', '') or ''} {place.get('region', '') or ''} {place.get('postal_code', '') or ''}, ".strip()
#     return location_string.rstrip(", ")
#   return location


def standardize_jobs(
    jobs: List[Dict], api_definition: ApiDefinition, company_name: str
) -> List[Dict]:
  response_config = api_definition["response"]
  root = response_config["root"]
  job_format = response_config["job_format"]
  parsed_jobs = []
  all_jobs = get_json_key(jobs, root)

  for job in all_jobs:
    formatted_job = {k: get_json_key(job, v)
                     for k, v in job_format.items()}
    formatted_job["location"] = json.dumps(formatted_job["location"])
    formatted_job["company"] = company_name

    formatted_job["years_of_experience"] = find_years_of_experience_in_job(job)

    if formatted_job.get("created_at"):
      try:
        formatted_job["created_at"] = datetime.strptime(
            formatted_job["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
        ).isoformat()
      except ValueError:
        formatted_job["created_at"] = datetime.now().isoformat()
    else:
      # TODO: Don't just set to now!
      formatted_job["created_at"] = datetime.now().isoformat()
    parsed_jobs.append(formatted_job)
  return parsed_jobs


def filter_jobs(formatted_jobs: List[Dict],
                criteria: Dict) -> Tuple[List[Dict], Dict]:
  filted_jobs = []
  stats = {"total": 0, "excluded": 0, "included": 0}
  exclude_stats = {
      "location": 0,
      "role": 0,
      "unspecified_years_of_experience": 0,
      "years_of_experience": 0,
  }
  for job in formatted_jobs:
    stats["total"] += 1

    should_include = should_include_job(job, criteria)
    if isinstance(should_include, dict) and should_include.get(
            "exclude_reason"):
      exclude_stats[should_include.get("exclude_reason")] += 1
      stats["excluded"] += 1
    elif isinstance(should_include, bool) and should_include:
      filted_jobs.append(job)
      stats["included"] += 1
    else:
      stats["excluded"] += 1
  return (filted_jobs, {"included_stats": stats,
          "excluded_stats": exclude_stats})
