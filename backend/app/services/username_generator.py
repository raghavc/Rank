from __future__ import annotations

import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


ADJECTIVES = (
    "silent", "swift", "calm", "bright", "quiet", "eager", "brave", "gentle",
    "happy", "lucky", "merry", "nimble", "polite", "proud", "rapid", "sly",
    "smooth", "snug", "steady", "stoic", "vivid", "witty", "zesty", "noble",
    "bold", "clever", "cosmic", "curious", "dapper", "dreamy", "earnest", "fancy",
    "fluffy", "grand", "humble", "jolly", "keen", "kind", "lively", "loyal",
    "mellow", "mighty", "patient", "plucky", "regal", "rustic", "serene",
    "sturdy", "tidy", "wise",
)

ANIMALS = (
    "otter", "fox", "panda", "owl", "lynx", "wolf", "bear", "hawk",
    "heron", "ibis", "moose", "newt", "puma", "raven", "robin", "seal",
    "swan", "tiger", "trout", "viper", "yak", "zebra", "badger", "beaver",
    "bison", "camel", "crane", "deer", "eagle", "falcon", "ferret", "gecko",
    "goose", "hare", "hedgehog", "horse", "koala", "mole", "octopus",
    "ostrich", "penguin", "rabbit", "rhino", "sparrow", "stoat", "swift",
    "turtle", "walrus", "weasel", "wombat",
)


def random_username() -> str:
    adj = random.choice(ADJECTIVES)
    animal = random.choice(ANIMALS)
    n = random.randint(0, 9999)
    return f"{adj}-{animal}-{n:04d}"


async def generate_unique(db: AsyncSession, max_attempts: int = 5) -> str:
    for _ in range(max_attempts):
        candidate = random_username()
        existing = await db.scalar(select(User.id).where(User.username == candidate))
        if existing is None:
            return candidate
    # Last-ditch: append more entropy.
    return f"{random_username()}-{random.randint(10000, 99999)}"
