"""
NexusTalent Database Layer
Async SQLAlchemy 2.0 Engine, Base Model & Session Management
"""

import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Any, Dict
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, Boolean, JSON, event
from backend.app.core.config import settings


# Async engine creation
connect_args = {}
if "postgresql" in settings.DATABASE_URL or "asyncpg" in settings.DATABASE_URL:
    connect_args = {"statement_cache_size": 0, "prepared_statement_cache_size": 0}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    """
    Universal Base Model for all NexusTalent entities.
    Enforces Multi-tenancy, UUID primary keys, and Auditing columns.
    """
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        default=settings.DEFAULT_TENANT_ID,
        index=True,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    extra_attributes: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        nullable=False
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary representation."""
        result = {}
        for c in self.__table__.columns:
            val = getattr(self, c.name)
            if isinstance(val, datetime):
                result[c.name] = val.isoformat()
            else:
                result[c.name] = val
        return result


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for yielding database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    import backend.app.modules.hrms.models  # noqa
    import backend.app.modules.recruitment.models  # noqa
    import backend.app.modules.attendance.models  # noqa
    import backend.app.modules.payroll.models  # noqa
    import backend.app.modules.performance.models  # noqa
    import backend.app.modules.helpdesk.models  # noqa
    import backend.app.core.notifications  # noqa

    try:
        from sqlalchemy import create_engine
        sync_engine = create_engine(settings.SYNC_DATABASE_URL, pool_pre_ping=True)
        Base.metadata.create_all(sync_engine)
        sync_engine.dispose()
    except Exception:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
