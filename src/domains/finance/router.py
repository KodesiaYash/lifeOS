"""
Finance domain API endpoints — placeholder for Phase 1 implementation.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def finance_domain_status() -> dict:
    return {"domain": "finance", "status": "scaffold", "version": "0.1.0"}
