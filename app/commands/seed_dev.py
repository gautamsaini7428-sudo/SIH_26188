"""
Development Database Seeding Command.

Explicitly seeds development accounts for officers, supervisor, and admin.
Run manually in development/staging:
    python -m app.commands.seed_dev
"""

import asyncio
import sys
from sqlalchemy import select, or_

from app.database import async_session_maker, init_db, close_db
from app.models import User
from app.auth import get_password_hash
from app.config import get_settings


DEMO_USERS = [
    {
        "email": "officer.attari@mha.gov.in",
        "username": "officer_attari",
        "password": "Password@123",
        "role": "OFFICER",
        "checkpoint_location": "Attari-Wagah Border",
    },
    {
        "email": "officer.petrapole@mha.gov.in",
        "username": "officer_petrapole",
        "password": "Password@123",
        "role": "OFFICER",
        "checkpoint_location": "Petrapole-Benapole Crossing",
    },
    {
        "email": "supervisor.delhi@mha.gov.in",
        "username": "supervisor_delhi",
        "password": "Password@123",
        "role": "SUPERVISOR",
        "checkpoint_location": "Border HQ (All Checkpoints)",
    },
    {
        "email": "admin@mha.gov.in",
        "username": "admin",
        "password": "Password@123",
        "role": "SUPERVISOR",
        "checkpoint_location": "Central Command",
    },
]


async def seed() -> None:
    settings = get_settings()
    print("Initializing database...")
    await init_db()

    print("Seeding development users...")
    async with async_session_maker() as db:
        count = 0
        for u in DEMO_USERS:
            username = settings.admin_username if u["email"] == "admin@mha.gov.in" else u["username"]
            res = await db.execute(select(User).where(or_(User.email == u["email"], User.username == username)))
            existing = res.scalar_one_or_none()
            if not existing:
                db_user = User(
                    email=u["email"],
                    username=username,
                    password_hash=get_password_hash(u["password"]),
                    role=u["role"],
                    checkpoint_location=u["checkpoint_location"],
                )
                db.add(db_user)
                count += 1
                print(f"  + Added {u['role']}: {u['email']} (user: {username})")
            else:
                print(f"  . Exists {u['role']}: {u['email']}")

        await db.commit()
        print(f"Seeding completed. {count} new accounts created.")

    await close_db()


if __name__ == "__main__":
    asyncio.run(seed())
