"""Tests for locale-aware monthly template variables."""

from __future__ import annotations

from datetime import UTC, datetime

from custom_components.document_sender.variables import monthly_variables


def test_monthly_variables_in_supported_languages() -> None:
    """Use the correct nominative and genitive month names."""
    now = datetime(2026, 7, 10, 12, tzinfo=UTC)

    assert monthly_variables("en", now)["month_name"] == "July"
    assert monthly_variables("pl-PL", now)["month_name_genitive"] == "lipca"
    assert monthly_variables("uk", now)["previous_month_name_genitive"] == "червня"
    assert monthly_variables("uk", now)["date"] == "2026-07-10"


def test_january_uses_previous_december_year() -> None:
    """Move the previous-month year back at the January boundary."""
    variables = monthly_variables("uk-UA", datetime(2026, 1, 5, tzinfo=UTC))

    assert variables["previous_month_name"] == "грудень"
    assert variables["previous_month_name_genitive"] == "грудня"
    assert variables["previous_month_year"] == "2025"
