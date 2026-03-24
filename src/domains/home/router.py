"""
Home & Environment domain API endpoints — placeholder for Phase 1 implementation.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def home_domain_status() -> dict:
    return {"domain": "home", "status": "scaffold", "version": "0.1.0"}
