"""test_payroll.py — Unit tests for the Employee Payroll Tracker."""

import pytest
from employee import FullTimeEmployee, ContractEmployee, Intern
from payroll import apply_tax, compute_payroll_details, generate_payslip, process_payroll
from utils import format_currency, divider, format_header


# ----------------------------------------------------------------------
# FullTimeEmployee
# ----------------------------------------------------------------------

class TestFullTimeEmployee:
    def test_gross_with_bonus(self):
        assert FullTimeEmployee("FT001", "Nziza Paul", 350_000, 50_000).calculate_salary() == 400_000

    def test_gross_without_bonus(self):
        assert FullTimeEmployee("FT001", "Nziza Paul", 350_000).calculate_salary() == 350_000

    def test_role(self):
        assert FullTimeEmployee("FT001", "Nziza Paul", 350_000).role() == "Full-Time Employee"

    def test_is_not_tax_exempt(self):
        assert FullTimeEmployee("FT001", "Nziza Paul", 350_000).is_tax_exempt is False

    def test_emp_id_uppercased(self):
        assert FullTimeEmployee("ft001", "Nziza Paul", 350_000).emp_id == "FT001"

    def test_name_stripped(self):
        assert FullTimeEmployee("FT001", "  Nziza Paul  ", 350_000).name == "Nziza Paul"

    def test_zero_salary_raises(self):
        with pytest.raises(ValueError):
            FullTimeEmployee("FT001", "Nziza Paul", 0)

    def test_negative_salary_raises(self):
        with pytest.raises(ValueError):
            FullTimeEmployee("FT001", "Nziza Paul", -1)

    def test_non_numeric_salary_raises(self):
        with pytest.raises(ValueError):
            FullTimeEmployee("FT001", "Nziza Paul", "high")  # type: ignore

    def test_negative_bonus_raises(self):
        with pytest.raises(ValueError):
            FullTimeEmployee("FT001", "Nziza Paul", 350_000, -1)

    def test_non_numeric_bonus_raises(self):
        with pytest.raises(ValueError):
            FullTimeEmployee("FT001", "Nziza Paul", 350_000, "big")  # type: ignore

    def test_empty_id_raises(self):
        with pytest.raises(ValueError):
            FullTimeEmployee("", "Nziza Paul", 350_000)

    def test_whitespace_id_raises(self):
        with pytest.raises(ValueError):
            FullTimeEmployee("   ", "Nziza Paul", 350_000)

    def test_empty_name_raises(self):
        with pytest.raises(ValueError):
            FullTimeEmployee("FT001", "", 350_000)

    def test_whitespace_name_raises(self):
        with pytest.raises(ValueError):
            FullTimeEmployee("FT001", "   ", 350_000)


# ----------------------------------------------------------------------
# ContractEmployee
# ----------------------------------------------------------------------

class TestContractEmployee:
    def test_gross(self):
        assert ContractEmployee("CT001", "Uwase Marie", 3_000, 160).calculate_salary() == 480_000

    def test_zero_hours_gives_zero_gross(self):
        assert ContractEmployee("CT001", "Uwase Marie", 3_000, 0).calculate_salary() == 0

    def test_role(self):
        assert ContractEmployee("CT001", "Uwase Marie", 3_000, 160).role() == "Contract Employee"

    def test_is_not_tax_exempt(self):
        assert ContractEmployee("CT001", "Uwase Marie", 3_000, 160).is_tax_exempt is False

    def test_hourly_rate_alias(self):
        assert ContractEmployee("CT001", "Uwase Marie", 3_000, 160).hourly_rate == 3_000

    def test_negative_hours_raises(self):
        with pytest.raises(ValueError):
            ContractEmployee("CT001", "Uwase Marie", 3_000, -1)

    def test_zero_rate_raises(self):
        with pytest.raises(ValueError):
            ContractEmployee("CT001", "Uwase Marie", 0, 160)

    def test_non_numeric_hours_raises(self):
        with pytest.raises(ValueError):
            ContractEmployee("CT001", "Uwase Marie", 3_000, "many")  # type: ignore


# ----------------------------------------------------------------------
# Intern
# ----------------------------------------------------------------------

class TestIntern:
    def test_gross_equals_stipend(self):
        assert Intern("IN001", "Amour Jean", 80_000).calculate_salary() == 80_000

    def test_role(self):
        assert Intern("IN001", "Amour Jean", 80_000).role() == "Intern"

    def test_is_not_tax_exempt(self):
        assert Intern("IN001", "Amour Jean", 80_000).is_tax_exempt is False

    def test_stipend_alias(self):
        assert Intern("IN001", "Amour Jean", 80_000).stipend == 80_000

    def test_zero_stipend_raises(self):
        with pytest.raises(ValueError):
            Intern("IN001", "Amour Jean", 0)

    def test_negative_stipend_raises(self):
        with pytest.raises(ValueError):
            Intern("IN001", "Amour Jean", -500)


# ----------------------------------------------------------------------
# Rwanda PAYE — apply_tax
# ----------------------------------------------------------------------

class TestApplyTax:
    def test_zero_income(self):
        assert apply_tax(0) == 0.0

    def test_within_first_bracket(self):
        assert apply_tax(20_000) == 0.0

    def test_at_first_bracket_ceiling(self):
        assert apply_tax(30_000) == 0.0

    def test_mid_second_bracket(self):
        """65,000: 0% on 30k + 20% on 35k = 7,000."""
        assert apply_tax(65_000) == 7_000.0

    def test_at_second_bracket_ceiling(self):
        """100,000: 0% on 30k + 20% on 70k = 14,000."""
        assert apply_tax(100_000) == 14_000.0

    def test_into_third_bracket(self):
        """150,000: 0 + 14,000 + 15,000 = 29,000."""
        assert apply_tax(150_000) == 29_000.0

    def test_large_gross(self):
        """400,000: 0 + 14,000 + 90,000 = 104,000."""
        assert apply_tax(400_000) == 104_000.0

    def test_negative_gross_raises(self):
        with pytest.raises(ValueError):
            apply_tax(-1)


# ----------------------------------------------------------------------
# compute_payroll_details
# ----------------------------------------------------------------------

class TestComputePayrollDetails:
    def test_keys_present(self):
        result = compute_payroll_details(FullTimeEmployee("FT001", "Nziza Paul", 350_000, 50_000))
        assert set(result.keys()) == {"emp_id", "name", "role", "gross", "tax", "net"}

    def test_full_time_figures(self):
        result = compute_payroll_details(FullTimeEmployee("FT001", "Nziza Paul", 350_000, 50_000))
        assert result["gross"] == 400_000
        assert result["tax"]   == 104_000
        assert result["net"]   == 296_000

    def test_contract_figures(self):
        result = compute_payroll_details(ContractEmployee("CT001", "Uwase Marie", 3_000, 160))
        assert result["gross"] == 480_000
        assert result["tax"]   == 128_000
        assert result["net"]   == 352_000

    def test_intern_pays_tax(self):
        result = compute_payroll_details(Intern("IN001", "Amour Jean", 80_000))
        assert result["gross"] == 80_000
        assert result["tax"]   == 10_000
        assert result["net"]   == 70_000

    def test_intern_below_threshold_no_tax(self):
        result = compute_payroll_details(Intern("IN001", "Amour Jean", 25_000))
        assert result["tax"] == 0.0
        assert result["net"] == 25_000

    def test_net_equals_gross_minus_tax(self):
        result = compute_payroll_details(FullTimeEmployee("FT002", "Kagabo Eric", 200_000))
        assert result["net"] == pytest.approx(result["gross"] - result["tax"])

    def test_zero_hours_contract_no_tax(self):
        result = compute_payroll_details(ContractEmployee("CT002", "Mugisha Alain", 3_000, 0))
        assert result["gross"] == 0.0
        assert result["tax"]   == 0.0
        assert result["net"]   == 0.0

    def test_process_payroll_returns_all(self):
        employees = [
            FullTimeEmployee("FT001", "Nziza Paul", 350_000, 50_000),
            ContractEmployee("CT001", "Uwase Marie", 3_000, 160),
            Intern("IN001", "Amour Jean", 80_000),
        ]
        results = process_payroll(employees)
        assert len(results) == 3
        assert [r["emp_id"] for r in results] == ["FT001", "CT001", "IN001"]


# ----------------------------------------------------------------------
# Utils
# ----------------------------------------------------------------------

class TestUtils:
    def test_format_currency_default(self):
        assert format_currency(296_000) == "$296,000.00"

    def test_format_currency_custom_symbol(self):
        assert format_currency(1_000, "RWF ") == "RWF 1,000.00"

    def test_format_currency_zero(self):
        assert format_currency(0) == "$0.00"

    def test_divider_default(self):
        assert divider() == "-" * 40

    def test_divider_custom(self):
        assert divider(10, "=") == "=========="

    def test_divider_zero_width_raises(self):
        with pytest.raises(ValueError):
            divider(0)

    def test_divider_negative_width_raises(self):
        with pytest.raises(ValueError):
            divider(-5)

    def test_format_header_contains_title(self):
        assert "PAYSLIPS" in format_header("PAYSLIPS")

    def test_format_header_three_lines(self):
        assert len(format_header("TEST").splitlines()) == 3

    def test_generate_payslip_fields(self):
        slip = generate_payslip(FullTimeEmployee("FT001", "Nziza Paul", 350_000, 50_000))
        assert "FT001"              in slip
        assert "Nziza Paul"         in slip
        assert "Full-Time Employee" in slip
        assert "$400,000.00"        in slip
        assert "$104,000.00"        in slip
        assert "$296,000.00"        in slip
