
from dataclasses import dataclass

from tabulate import tabulate


def ratio(numerator: int, denominator: int) -> float:
  return round(float(int(numerator) / int(denominator)), 4)


@dataclass
class ParseJobsStats:
  total: int = 0
  passed_all_filters: int = 0
  years_of_experience_success_count: int = 0
  role_success_count: int = 0
  date_posted_success_count: int = 0
  location_success_count: int = 0
  # Failure count
  location_failure_count: int = 0
  role_failure_count: int = 0
  unspecified_years_of_experience_failure_count: int = 0
  not_enough_years_of_experience_failure_count: int = 0
  custom_filter_failure_count: int = 0

  def print_stats(self):
    data = [
        ["Total", self.total, ""],
        ["Failure", "", ""],
        ["Location failure", self.location_failure_count,
         f"{ratio(self.location_failure_count, self.total)}"],
        ["Not enough years of experience failure", self.not_enough_years_of_experience_failure_count,
         f"{ratio(self.not_enough_years_of_experience_failure_count, self.total)}"],
        ["Unspecified years of experience failure", self.unspecified_years_of_experience_failure_count,
         f"{ratio(self.unspecified_years_of_experience_failure_count, self.total)}"],
        ["Role failure", self.role_failure_count,
         f"{ratio(self.role_failure_count, self.total)}"],
        ["Custom filter failure", self.custom_filter_failure_count,
         f"{ratio(self.custom_filter_failure_count, self.total)}"],
        ["Total failure", self.total - self.passed_all_filters,
         f"{ratio(self.total - self.passed_all_filters, self.total)}"],
        ["--", "", ""],
        ["Success", "", ""],
        ["Ignore me for now: Date posted < time success", self.date_posted_success_count,
         f"{ratio(self.date_posted_success_count, self.total)}"],
        ["Location success", self.location_success_count,
         f"{ratio(self.location_success_count, self.total)}"],
        ["Years of experience success", self.years_of_experience_success_count,
         f"{ratio(self.years_of_experience_success_count, self.total)}"],

        ["Passed all filters", self.passed_all_filters,
         f"{ratio(self.passed_all_filters, self.total)}"],
    ]
    print(tabulate(data, tablefmt="simple"))
