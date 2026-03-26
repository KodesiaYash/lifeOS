"""
FastAPI dependency injection for database sessions.

Single-user mode: No tenant or user context required.
The app runs for whoever is running it locally.
"""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.database import get_db


# Type alias for cleaner dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
