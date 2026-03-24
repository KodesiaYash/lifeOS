"""
FastAPI dependency injection for database sessions, tenant context, and current user.
"""
import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.database import get_db


async def get_current_tenant_id(
    x_tenant_id: Annotated[str | None, Header()] = None,
) -> uuid.UUID:
    """
    Extract tenant ID from request header.
    In production, this would come from the JWT token.
    For MVP, it's passed as a header for simplicity.
    """
    if not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-Id header is required",
        )
    try:
        return uuid.UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-Id must be a valid UUID",
        )


async def get_current_user_id(
    x_user_id: Annotated[str | None, Header()] = None,
) -> uuid.UUID:
    """
    Extract user ID from request header.
    In production, this would come from the JWT token.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-User-Id header is required",
        )
    try:
        return uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-User-Id must be a valid UUID",
        )


# Type aliases for cleaner dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]
TenantId = Annotated[uuid.UUID, Depends(get_current_tenant_id)]
UserId = Annotated[uuid.UUID, Depends(get_current_user_id)]
