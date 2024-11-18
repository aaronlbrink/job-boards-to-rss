import json
from typing import Dict

import pytest

from src.parse import (find_years_of_experience_in_job, location_match,
                       role_match)
from tests.cases import location_tests, role_tests, years_of_experience


# TODO: Criterias should be frozen to something like criterias.test.json
# so that my actual criterias can keep getting updated without upsetting
# test cases.
def import_criterias() -> Dict:
  try:
    with open("src/criteria.json", "r") as f:
      return json.load(f)
  except FileNotFoundError:
    print(
        "Error: criteria.json not found. Please ensure this file exists in the current directory."
    )


class TestFilters:
  @pytest.mark.parametrize("locations,expected", location_tests)
  def test_location_match(self, locations, expected):
    criteria = import_criterias()
    assert location_match(locations, criteria) == expected

  @pytest.mark.parametrize("job_json,expected", years_of_experience)
  def test_find_years_of_experience_in_job(self, job_json, expected):
    assert find_years_of_experience_in_job(job_json) == expected

  @pytest.mark.parametrize("title,description,expected", role_tests)
  def test_role_match(self, title, description, expected):
    criteria = import_criterias()
    rm = role_match(title, description, criteria)
    assert isinstance(rm, list)
    if len(expected) == 0:
      assert rm == expected
    else:
      for role in rm:
        assert role in expected
