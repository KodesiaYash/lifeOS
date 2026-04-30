"""
Inbound communication pipeline.

This service enforces the architecture contract:

adapter -> communication persistence -> orchestrator -> event bus -> dispatcher
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from src.communication.dispatcher import dispatch_message
from src.communication.schemas import DeliveryReceipt, NormalizedInboundEvent, OutboundMessage
from src.communication.service import CommunicationService
from src.events.bus import EventBus, event_bus
from src.events.schemas import PlatformEvent
from src.kernel.orchestrator import GlobalOrchestrator, OrchestratorContext

Dispatcher = Callable[[OutboundMessage], Awaitable[DeliveryReceipt]]


@dataclass
class InboundProcessingResult:
    status: str
    channel_type: str
    idempotency_key: str
    bot_id: str | None = None
    domain: str | None = None
    response_text: str | None = None
    conversation_id: str | None = None
    correlation_id: str | None = None


class InboundMessagePipeline:
    """Handles the full persisted inbound-to-outbound interaction flow."""

    def __init__(
        self,
        session: AsyncSession,
        *,
        orchestrator: GlobalOrchestrator | None = None,
        dispatcher: Dispatcher = dispatch_message,
        event_bus_instance: EventBus | None = None,
    ) -> None:
        self.session = session
        self.communication = CommunicationService(session)
        self.orchestrator = orchestrator or GlobalOrchestrator(session)
        self.dispatcher = dispatcher
        self.event_bus = event_bus_instance or event_bus

    async def handle(
        self,
        *,
        channel_account_id: uuid.UUID,
        event: NormalizedInboundEvent,
        bot_id: str | None = None,
        target_domain: str | None = None,
        user_name: str | None = None,
    ) -> InboundProcessingResult:
        """Persist inbound, orchestrate a reply, dispatch outbound, and emit lifecycle events."""
        stored_message = await self.communication.process_inbound(
            channel_account_id=channel_account_id,
            event=event,
        )
        if stored_message is None:
            return InboundProcessingResult(
                status="duplicate",
                channel_type=event.channel_type,
                idempotency_key=event.idempotency_key,
                bot_id=bot_id,
                domain=target_domain,
            )

        ctx = OrchestratorContext(
            user_message=event.text or "",
            conversation_id=stored_message.conversation_id,
            channel_type=event.channel_type,
            session_id=str(stored_message.conversation_id),
            message_id=stored_message.id,
            bot_id=bot_id,
            target_domain=target_domain,
            channel_user_id=event.channel_user_id,
            external_chat_id=event.external_chat_id or event.channel_user_id,
            user_name=user_name,
            content_type=event.content_type,
        )
        response_text = await self.orchestrator.process(ctx)

        outbound = OutboundMessage(
            channel_type=event.channel_type,
            channel_account_id=channel_account_id,
            recipient_channel_id=event.external_chat_id or event.channel_user_id,
            text=response_text,
        )
        receipt = await self.dispatcher(outbound)

        await self.communication.store_outbound(
            conversation_id=stored_message.conversation_id,
            text=response_text,
            channel_message_id=receipt.channel_message_id,
            correlation_id=ctx.correlation_id,
        )

        await self._emit_dispatch_event(
            ctx=ctx,
            event=event,
            receipt=receipt,
        )

        return InboundProcessingResult(
            status="processed",
            channel_type=event.channel_type,
            idempotency_key=event.idempotency_key,
            bot_id=bot_id,
            domain=ctx.intent.get("domain") if ctx.intent else target_domain,
            response_text=response_text,
            conversation_id=str(stored_message.conversation_id),
            correlation_id=str(ctx.correlation_id),
        )

    async def _emit_dispatch_event(
        self,
        *,
        ctx: OrchestratorContext,
        event: NormalizedInboundEvent,
        receipt: DeliveryReceipt,
    ) -> None:
        dispatch_event = PlatformEvent(
            event_type="communication.message_sent",
            event_category="communication",
            domain=ctx.intent.get("domain") if ctx.intent else None,
            correlation_id=ctx.correlation_id,
            payload={
                "message_id": str(ctx.message_id) if ctx.message_id else None,
                "conversation_id": str(ctx.conversation_id) if ctx.conversation_id else None,
                "channel_type": ctx.channel_type,
                "recipient_channel_id": event.external_chat_id or event.channel_user_id,
                "bot_id": ctx.bot_id,
                "channel_message_id": receipt.channel_message_id,
                "dispatch_status": receipt.status,
            },
            source="communication",
        )
        await self.event_bus.publish(dispatch_event, session=self.session)
