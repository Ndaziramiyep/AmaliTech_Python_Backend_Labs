"""
tests/test_payroll.py
Unit tests for the Employee Payroll Tracker.

Covers:
    - Employee subclass construction and property validation
    - Rwanda PAYE tax bracket logic (apply_tax)
    - Payroll detail computation (compute_payroll_details)
    - Formatting helpers (format_currency, divider, format_header)
"""

import pytest
from employee import FullTimeEmployee, ContractEmployee, Intern
from payroll import apply_tax, compute_payroll_details, generate_payslip
from utils import format_currency, divider, format_header


# -----------------------------------------------------------------------
# Employee construction & property validation
# -----------------------------------------------------------------------

class TestFullTimeEmployee:
    def test_gross_salary_with_bonus(self):
        emp = FullTimeEmployee("FT001", "Nziza Paul", 350_000, 50_000)
        assert emp.calculate_salary() == 400_000

    def test_gross_salary_no_bonus(self):
        emp = FullTimeEmployee("FT001", "Nziza Paul", 350_000)
        assert emp.calculate_salary() == 350_000

    def test_role_label(self):
        emp = FullTimeEmployee("FT001", "Nziza Paul", 350_000)
        assert emp.role() == "Full-Time Employee"

    def test_is_not_tax_exempt(self):
        emp = FullTimeEmployee("FT001", "Nziza Paul", 350_000)
        assert emp.is_tax_exempt is False

    def test_invalid_base_salary_raises(self):
        with pytest.raises(ValueError):
            FullTimeEmployee("FT001", "Nziza Paul", 0)

    def test_negative_base_salary_raises(self):
        with pytest.raises(ValueError):
            FullTimeEmployee("FT001", "Nziza Paul", -1000)

    def test_negative_bonus_raises(self):
        with pytest.raises(ValueError):
            FullTimeEmployee("FT001", "Nziza Paul", 350_000, -1)


class TestContractEmployee:
    def test_gross_salary(self):
        emp = ContractEmployee("CT001", "Uwase Marie", 3_000, 160)
        assert emp.calculate_salary() == 480_000

    def test_zero_hours_gives_zero_gross(self):
        emp = ContractEmployee("CT001", "Uwase Marie", 3_000, 0)
        assert emp.calculate_salary() == 0

    def test_role_label(self):
        emp = ContractEmployee("CT001", "Uwase Marie", 3_000, 160)
        assert emp.role() == "Contract Employee"

    def test_is_not_tax_exempt(self):
        emp = ContractEmployee("CT001", "Uwase Marie", 3_000, 160)
        assert emp.is_tax_exempt is False

    def test_negative_hours_raises(self):
        with pytest.raises(ValueError):
            ContractEmployee("CT001", "Uwase Marie", 3_000, -1)

    def test_invalid_hourly_rate_raises(self):
        with pytest.raises(ValueError):
            ContractEmployee("CT001", "Uwase Marie", 0, 160)

    def test_hourly_rate_alias(self):
        emp = ContractEmployee("CT001", "Uwase Marie", 3_000, 160)
        assert emp.hourly_rate == 3_000


class TestIntern:
    def test_gross_salary_equals_stipend(self):
        emp = Intern("IN001", "Amour Jean", 80_000)
        assert emp.calculate_salary() == 80_000

    def test_role_label(self):
        emp = Intern("IN001", "Amour Jean", 80_000)
        assert emp.role() == "Intern"

    def test_is_not_tax_exempt(self):
        """Interns pay Rwanda PAYE — is_tax_exempt must be False."""
        emp = Intern("IN001", "Amour Jean", 80_000)
        assert emp.is_tax_exempt is False

    def test_stipend_alias(self):
        emp = Intern("IN001", "Amour Jean", 80_000)
        assert emp.stipend == 80_000

    def test_invalid_stipend_raises(self):
        with pytest.raises(ValueError):
            Intern("IN001", "Amour Jean", 0)


# -----------------------------------------------------------------------
# Rwanda PAYE tax brackets
# -----------------------------------------------------------------------

class TestApplyTax:
    def test_below_first_bracket_no_tax(self):
        """Income <= 30,000 RWF is tax-free."""
        assert apply_tax(30_000) == 0.0

    def test_zero_income_no_tax(self):
        assert apply_tax(0) == 0.0

    def test_exactly_at_second_bracket_upper(self):
        """100,000 RWF: 0% on first 30k + 20% on 30k–100k = 14,000."""
        assert apply_tax(100_000) == 14_000.0

    def test_into_third_bracket(self):
        """150,000 RWF: 0 + 14,000 + 15,000 = 29,000."""
        assert apply_tax(150_000) == 29_000.0

    def test_400000_gross(self):
        """400,000 RWF: 0 + 14,000 + 90,000 = 104,000."""
        assert apply_tax(400_000) == 104_000.0

    def test_only_second_bracket(self):
        """65,000 RWF: 0% on 30k + 20% on 35k = 7,000."""
        assert apply_tax(65_000) == 7_000.0


# -----------------------------------------------------------------------
# Payroll detail computation
# -----------------------------------------------------------------------

class TestComputePayrollDetails:
    def test_full_time_keys_present(self):
        emp = FullTimeEmployee("FT001", "Nziza Paul", 350_000, 50_000)
        result = compute_payroll_details(emp)
        assert set(result.keys()) == {"emp_id", "name", "role", "gross", "tax", "net"}

    def test_full_time_gross_tax_net(self):
        emp = FullTimeEmployee("FT001", "Nziza Paul", 350_000, 50_000)
        result = compute_payroll_details(emp)
        assert result["gross"] == 400_000
        assert result["tax"]   == 104_000
        assert result["net"]   == 296_000

    def test_contract_gross_tax_net(self):
        emp = ContractEmployee("CT001", "Uwase Marie", 3_000, 160)
        result = compute_payroll_details(emp)
        assert result["gross"] == 480_000
        assert result["tax"]   == 128_000
        assert result["net"]   == 352_000

    def test_intern_pays_tax(self):
        """Interns are subject to PAYE — tax must be > 0 for stipend > 30,000."""
        emp = Intern("IN001", "Amour Jean", 80_000)
        result = compute_payroll_details(emp)
        assert result["gross"] == 80_000
        assert result["tax"]   == 10_000
        assert result["net"]   == 70_000

    def test_intern_below_threshold_no_tax(self):
        """Intern stipend <= 30,000 falls in the 0% band — no tax."""
        emp = Intern("IN001", "Amour Jean", 25_000)
        result = compute_payroll_details(emp)
        assert result["tax"] == 0.0
        assert result["net"] == 25_000

    def test_net_equals_gross_minus_tax(self):
        emp = FullTimeEmployee("FT002", "Kagabo Eric", 200_000)
        result = compute_payroll_details(emp)
        assert result["net"] == pytest.approx(result["gross"] - result["tax"])


# -----------------------------------------------------------------------
# Formatting helpers
# -----------------------------------------------------------------------

class TestUtils:
    def test_format_currency_default_symbol(self):
        assert format_currency(296_000) == "$296,000.00"

    def test_format_currency_custom_symbol(self):
        assert format_currency(1_000, "RWF ") == "RWF 1,000.00"

    def test_format_currency_zero(self):
        assert format_currency(0) == "$0.00"

    def test_divider_default(self):
        assert divider() == "-" * 40

    def test_divider_custom(self):
        assert divider(10, "=") == "=========="

    def test_format_header_contains_title(self):
        header = format_header("PAYSLIPS")
        assert "PAYSLIPS" in header

    def test_format_header_has_three_lines(self):
        header = format_header("TEST")
        assert len(header.splitlines()) == 3

    def test_generate_payslip_contains_fields(self):
        emp = FullTimeEmployee("FT001", "Nziza Paul", 350_000, 50_000)
        slip = generate_payslip(emp)
        assert "FT001" in slip
        assert "Nziza Paul" in slip
        assert "Full-Time Employee" in slip
        assert "$400,000.00" in slip
        assert "$104,000.00" in slip
        assert "$296,000.00" in slip
