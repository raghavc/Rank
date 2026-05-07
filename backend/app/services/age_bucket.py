from __future__ import annotations

from datetime import date


AGE_BUCKETS = ("18-24", "25-29", "30-34", "35-39", "40-49", "50+")


def age_for(dob: date, today: date | None = None) -> int:
    today = today or date.today()
    years = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    return years


def bucket_for(dob: date, today: date | None = None) -> str:
    age = age_for(dob, today)
    if age < 18:
        raise ValueError("must be 18 or older")
    if age <= 24:
        return "18-24"
    if age <= 29:
        return "25-29"
    if age <= 34:
        return "30-34"
    if age <= 39:
        return "35-39"
    if age <= 49:
        return "40-49"
    return "50+"
