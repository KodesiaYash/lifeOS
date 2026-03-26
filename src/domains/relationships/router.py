"""
Relationships domain API endpoints — placeholder for Phase 1 implementation.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def relationships_domain_status() -> dict:
    return {"domain": "relationships", "status": "scaffold", "version": "0.1.0"}
