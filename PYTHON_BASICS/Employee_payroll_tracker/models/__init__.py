"""models/__init__.py — Exposes all employee model classes from the models package."""

from models.Employee import Employee
from models.FullTimeEmployee import FullTimeEmployee
from models.ContractEmployee import ContractEmployee
from models.Intern import Intern

__all__ = ["Employee", "FullTimeEmployee", "ContractEmployee", "Intern"]
