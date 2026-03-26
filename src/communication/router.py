"""
API endpoints for the communication layer: webhooks and message endpoints.

Single-user mode: No tenant context required.
"""

from fastapi import APIRouter, HTTPException, Request, status

from src.dependencies import DbSession

router = APIRouter()


@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, db: DbSession) -> dict:
    """
    WhatsApp Cloud API webhook endpoint.
    Handles both verification (GET) and message events (POST).
    """
    body = await request.json()

    # Webhook verification challenge (GET is handled by FastAPI separately)
    if "hub.challenge" in dict(request.query_params):
        return {"hub.challenge": request.query_params["hub.challenge"]}

    from src.communication.adapters.whatsapp import WhatsAppAdapter

    adapter = WhatsAppAdapter()
    event = await adapter.normalize_inbound(body)
    if event is None:
        return {"status": "ignored"}

    return {"status": "received", "idempotency_key": event.idempotency_key}


@router.get("/webhooks/whatsapp")
async def whatsapp_webhook_verify(request: Request) -> int:
    """WhatsApp webhook verification (hub.challenge)."""
    params = dict(request.query_params)
    challenge = params.get("hub.challenge")
    if challenge:
        return int(challenge)
    raise HTTPException(status_code=400, detail="Missing hub.challenge")


@router.post("/webhooks/telegram")
async def telegram_webhook(request: Request, db: DbSession) -> dict:
    """Telegram Bot API webhook endpoint."""
    body = await request.json()

    from src.communication.adapters.telegram import TelegramAdapter

    adapter = TelegramAdapter()
    event = await adapter.normalize_inbound(body)
    if event is None:
        return {"status": "ignored"}

    return {"status": "received", "idempotency_key": event.idempotency_key}


@router.post("/messages", status_code=status.HTTP_201_CREATED)
async def send_message_via_rest(
    payload: dict,
    db: DbSession,
) -> dict:
    """
    REST API message endpoint.
    Accepts a message and processes it.
    """
    from src.communication.adapters.rest_api import RestApiAdapter

    adapter = RestApiAdapter()
    event = await adapter.normalize_inbound(payload)
    if event is None:
        raise HTTPException(status_code=400, detail="Could not parse message")

    # TODO: Wire into the global orchestrator for full processing
    return {
        "status": "received",
        "channel_type": "rest_api",
        "idempotency_key": event.idempotency_key,
    }
