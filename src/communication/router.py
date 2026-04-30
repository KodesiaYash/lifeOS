"""
API endpoints for the communication layer: webhooks and message endpoints.

Single-user mode: No tenant context required.
"""

import uuid

from fastapi import APIRouter, HTTPException, Request, status

from src.communication.pipeline import InboundMessagePipeline
from src.config import settings
from src.dependencies import DbSession

router = APIRouter()


def _get_channel_account_id(request: Request, channel_type: str) -> uuid.UUID:
    bindings = getattr(request.app.state, "channel_account_ids", {})
    account_id = bindings.get(channel_type)
    if account_id is None:
        raise HTTPException(status_code=503, detail=f"No configured channel account for {channel_type}")
    return account_id


def _telegram_sender_name(raw_payload: dict) -> str | None:
    message = raw_payload.get("message", {})
    sender = message.get("from", {})
    first_name = sender.get("first_name")
    last_name = sender.get("last_name")
    name = " ".join(part for part in [first_name, last_name] if part)
    return name or sender.get("username")


async def _process_domain_event(
    *,
    request: Request,
    db,
    event,
    target_domain: str,
    bot_id: str | None = None,
    user_name: str | None = None,
) -> dict:
    account_id = _get_channel_account_id(request, event.channel_type)
    event.channel_account_id = account_id
    pipeline = InboundMessagePipeline(db)
    result = await pipeline.handle(
        channel_account_id=account_id,
        event=event,
        bot_id=bot_id,
        target_domain=target_domain,
        user_name=user_name,
    )

    return {
        "status": result.status,
        "channel_type": result.channel_type,
        "bot_id": result.bot_id,
        "domain": result.domain,
        "idempotency_key": result.idempotency_key,
        "response_text": result.response_text,
        "conversation_id": result.conversation_id,
        "correlation_id": result.correlation_id,
    }


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
    from src.communication.adapters.telegram import TelegramAdapter

    adapter = TelegramAdapter()
    raw_body = await request.body()
    if not await adapter.verify_webhook(dict(request.headers), raw_body):
        raise HTTPException(status_code=403, detail="Invalid Telegram webhook secret")

    body = await request.json()
    event = await adapter.normalize_inbound(body)
    if event is None:
        return {"status": "ignored"}

    if not settings.DUTCH_TUTOR_ENABLED:
        raise HTTPException(status_code=503, detail="Dutch tutor bot is disabled")

    return await _process_domain_event(
        request=request,
        db=db,
        event=event,
        target_domain="dutch_tutor",
        bot_id=settings.DUTCH_TUTOR_BOT_ID,
        user_name=_telegram_sender_name(body),
    )


@router.post("/messages", status_code=status.HTTP_201_CREATED)
async def send_message_via_rest(
    payload: dict,
    request: Request,
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

    bot_id = str(payload.get("bot_id", settings.DUTCH_TUTOR_BOT_ID))
    return await _process_domain_event(
        request=request,
        db=db,
        event=event,
        target_domain="dutch_tutor",
        bot_id=bot_id,
        user_name=payload.get("user_name"),
    )
