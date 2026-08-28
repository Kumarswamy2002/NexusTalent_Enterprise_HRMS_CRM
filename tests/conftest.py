"""
Pytest configuration for NexusTalent Enterprise test suite.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import asyncio
from backend.app.core.database import init_db, AsyncSessionLocal
from backend.app.seeds.enterprise_seeder import seed_enterprise_data

# Ensure all models are imported so Base.metadata knows all tables
import backend.app.modules.hrms.models
import backend.app.modules.recruitment.models
import backend.app.modules.attendance.models
import backend.app.modules.payroll.models
import backend.app.modules.performance.models
import backend.app.modules.helpdesk.models
import backend.app.core.audit
import backend.app.core.notifications


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Initializes tables and seeds test data before test execution."""
    async def _init():
        await init_db()
        async with AsyncSessionLocal() as session:
            await seed_enterprise_data(session)

    asyncio.run(_init())
