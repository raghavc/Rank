from __future__ import annotations

import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


# Max username is 11 chars. Format: adj-noun-NN (e.g. sly-fox-42)
# Keep adjectives ≤4 chars, nouns ≤3 chars → adj(4) + dash + noun(3) + dash + NN(2) = 11

ADJECTIVES = (
    "sly", "bold", "calm", "cool", "keen", "kind", "fast", "wise",
    "wild", "warm", "epic", "fair", "gold", "grim", "hazy", "icy",
    "lazy", "lean", "loud", "mad", "neat", "odd", "pale", "raw",
    "red", "rich", "safe", "shy", "slim", "snug", "soft", "tall",
    "tidy", "tiny", "true", "vast", "viv", "wry", "zen", "zap",
)

ANIMALS = (
    "fox", "owl", "yak", "eel", "bat", "cat", "cow", "dog",
    "elk", "emu", "hen", "jay", "koi", "ram", "rat", "bee",
    "ant", "ape", "cod", "cub", "doe", "gnu", "hog", "imp",
)


def random_username() -> str:
    adj = random.choice(ADJECTIVES)
    animal = random.choice(ANIMALS)
    n = random.randint(0, 99)
    return f"{adj}-{animal}-{n:02d}"


async def generate_unique(db: AsyncSession, max_attempts: int = 10) -> str:
    for _ in range(max_attempts):
        candidate = random_username()
        existing = await db.scalar(select(User.id).where(User.username == candidate))
        if existing is None:
            return candidate
    # Last-ditch: use 3-digit number, still fits 11 chars with short adj/noun
    adj = random.choice(("sly", "shy", "mad", "odd", "raw", "red"))
    animal = random.choice(("fox", "owl", "yak", "eel", "bat"))
    return f"{adj}-{animal}-{random.randint(100, 999)}"
