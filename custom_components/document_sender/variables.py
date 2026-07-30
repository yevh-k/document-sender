"""Locale-aware variables for monthly document templates."""

from __future__ import annotations

from datetime import date, datetime
from typing import Final

MonthForms = tuple[tuple[str, str], ...]

_MONTHS: Final[dict[str, MonthForms]] = {
    "en": (
        ("January", "January"),
        ("February", "February"),
        ("March", "March"),
        ("April", "April"),
        ("May", "May"),
        ("June", "June"),
        ("July", "July"),
        ("August", "August"),
        ("September", "September"),
        ("October", "October"),
        ("November", "November"),
        ("December", "December"),
    ),
    "pl": (
        ("styczeń", "stycznia"),
        ("luty", "lutego"),
        ("marzec", "marca"),
        ("kwiecień", "kwietnia"),
        ("maj", "maja"),
        ("czerwiec", "czerwca"),
        ("lipiec", "lipca"),
        ("sierpień", "sierpnia"),
        ("wrzesień", "września"),
        ("październik", "października"),
        ("listopad", "listopada"),
        ("grudzień", "grudnia"),
    ),
    "uk": (
        ("січень", "січня"),
        ("лютий", "лютого"),
        ("березень", "березня"),
        ("квітень", "квітня"),
        ("травень", "травня"),
        ("червень", "червня"),
        ("липень", "липня"),
        ("серпень", "серпня"),
        ("вересень", "вересня"),
        ("жовтень", "жовтня"),
        ("листопад", "листопада"),
        ("грудень", "грудня"),
    ),
}


def monthly_variables(language: str, local_now: date | datetime) -> dict[str, str]:
    """Return monthly variables for a date in Home Assistant's timezone."""
    today = local_now.date() if isinstance(local_now, datetime) else local_now
    language_code = language.lower().split("-", maxsplit=1)[0]
    months = _MONTHS.get(language_code, _MONTHS["en"])
    previous_month = 12 if today.month == 1 else today.month - 1
    previous_year = today.year - 1 if today.month == 1 else today.year
    current_forms = months[today.month - 1]
    previous_forms = months[previous_month - 1]
    return {
        "month_name": current_forms[0],
        "month_name_genitive": current_forms[1],
        "previous_month_name": previous_forms[0],
        "previous_month_name_genitive": previous_forms[1],
        "year": str(today.year),
        "previous_month_year": str(previous_year),
        "date": today.isoformat(),
    }
