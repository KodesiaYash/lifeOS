"""Dutch tutor domain API endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.domains.dutch_tutor.service import DutchTutorService

router = APIRouter()


class TranslateRequest(BaseModel):
    word: str = Field(..., min_length=1, max_length=64)


class TranslateResponse(BaseModel):
    input_word: str
    detected_language: str
    dutch_word: str
    english_word: str
    back_to_dutch: str
    known_word: bool
    reply_text: str


@router.get("/status")
async def dutch_tutor_status() -> dict[str, str]:
    return {"domain": "dutch_tutor", "status": "active", "version": "0.1.0"}


@router.post("/translate", response_model=TranslateResponse)
async def translate_word(payload: TranslateRequest) -> TranslateResponse:
    result = DutchTutorService.translate_roundtrip(payload.word)
    return TranslateResponse(
        input_word=result.input_word,
        detected_language=result.detected_language,
        dutch_word=result.dutch_word,
        english_word=result.english_word,
        back_to_dutch=result.back_to_dutch,
        known_word=result.known_word,
        reply_text=result.reply_text,
    )
