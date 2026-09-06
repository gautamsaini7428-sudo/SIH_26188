from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    import app.models  # ensure all models are registered on Base.metadata
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Auto-migrate new columns for existing verifications table
        verification_cols = [
            ("reason", "TEXT"),
            ("document_type", "VARCHAR(30)"),
            ("checkpoint_location", "VARCHAR(100)"),
            ("risk_score", "INTEGER"),
            ("extracted_fields_json", "TEXT"),
            ("full_response_json", "TEXT"),
            ("officer_email", "VARCHAR(255)"),
        ]
        for col_name, col_type in verification_cols:
            try:
                await conn.execute(text(f"ALTER TABLE verifications ADD COLUMN {col_name} {col_type}"))
            except Exception:
                pass  # column already exists

        # Auto-migrate new columns for existing users table
        user_cols = [
            ("email", "VARCHAR(255)"),
            ("role", "VARCHAR(20) DEFAULT 'OFFICER'"),
            ("checkpoint_location", "VARCHAR(100)"),
        ]
        for col_name, col_type in user_cols:
            try:
                await conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
            except Exception:
                pass

    # Ensure demo users are present
    try:
        from app.auth import get_password_hash
        from app.models import User
        from sqlalchemy import select, or_

        demo_users = [
            {
                "email": "officer.attari@mha.gov.in",
                "username": "officer_attari",
                "password_hash": get_password_hash("Password@123"),
                "role": "OFFICER",
                "checkpoint_location": "Attari-Wagah Border",
            },
            {
                "email": "officer.petrapole@mha.gov.in",
                "username": "officer_petrapole",
                "password_hash": get_password_hash("Password@123"),
                "role": "OFFICER",
                "checkpoint_location": "Petrapole-Benapole Crossing",
            },
            {
                "email": "supervisor.delhi@mha.gov.in",
                "username": "supervisor_delhi",
                "password_hash": get_password_hash("Password@123"),
                "role": "SUPERVISOR",
                "checkpoint_location": "Border HQ (All Checkpoints)",
            },
            {
                "email": "admin@mha.gov.in",
                "username": "admin",
                "password_hash": get_password_hash("Password@123"),
                "role": "SUPERVISOR",
                "checkpoint_location": "Central Command",
            },
        ]
        async with async_session_maker() as session:
            for u_data in demo_users:
                existing = await session.execute(
                    select(User).where(or_(User.email == u_data["email"], User.username == u_data["username"]))
                )
                if not existing.scalar_one_or_none():
                    session.add(User(**u_data))
            await session.commit()
    except Exception:
        pass


async def close_db() -> None:
    await engine.dispose()