from datetime import date

import pytest

from app.services.age_bucket import bucket_for


def test_bucket_18_24() -> None:
    today = date(2026, 5, 6)
    assert bucket_for(date(2008, 5, 6), today) == "18-24"
    assert bucket_for(date(2002, 5, 7), today) == "18-24"


def test_bucket_25_29() -> None:
    today = date(2026, 5, 6)
    assert bucket_for(date(2001, 5, 6), today) == "25-29"
    assert bucket_for(date(1997, 5, 7), today) == "25-29"


def test_bucket_30_34() -> None:
    today = date(2026, 5, 6)
    assert bucket_for(date(1996, 5, 6), today) == "30-34"
    assert bucket_for(date(1992, 5, 7), today) == "30-34"


def test_bucket_35_39() -> None:
    today = date(2026, 5, 6)
    assert bucket_for(date(1991, 5, 6), today) == "35-39"
    assert bucket_for(date(1987, 5, 7), today) == "35-39"


def test_bucket_40_49() -> None:
    today = date(2026, 5, 6)
    assert bucket_for(date(1986, 5, 6), today) == "40-49"
    assert bucket_for(date(1977, 5, 7), today) == "40-49"


def test_bucket_50_plus() -> None:
    today = date(2026, 5, 6)
    assert bucket_for(date(1976, 5, 6), today) == "50+"
    assert bucket_for(date(1950, 1, 1), today) == "50+"


def test_too_young() -> None:
    today = date(2026, 5, 6)
    with pytest.raises(ValueError):
        bucket_for(date(2010, 5, 6), today)
