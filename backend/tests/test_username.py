import re

from app.services.username_generator import random_username


def test_format() -> None:
    name = random_username()
    assert re.match(r"^[a-z]+-[a-z]+-\d{4}$", name), name


def test_uniqueness_pressure() -> None:
    names = {random_username() for _ in range(2000)}
    # We expect way more than 90% uniqueness across 2000 draws given 50*50*10000 space.
    assert len(names) / 2000 > 0.95
