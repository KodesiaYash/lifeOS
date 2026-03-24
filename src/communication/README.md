# Communication Module (`src/communication/`)

Generic communication layer with pluggable channel adapters for WhatsApp, Telegram, and REST API.

## Contents

| File | Purpose |
|------|---------|
| `schemas.py` | `NormalizedInboundEvent`, `OutboundMessage`, `DeliveryReceipt`, enums |
| `models.py` | SQLAlchemy models: Channel, ChannelAccount, ChannelIdentity, Conversation, Message, MessageEvent, Attachment |
| `repository.py` | Database access for all communication entities |
| `service.py` | `CommunicationService` — inbound processing, identity resolution, idempotency |
| `dispatcher.py` | Outbound message dispatch with retry logic and adapter routing |
| `router.py` | Webhook endpoints for WhatsApp/Telegram + REST message endpoint |
| `adapters/base.py` | `ChannelAdapter` ABC |
| `adapters/whatsapp.py` | WhatsApp Cloud API adapter (stub) |
| `adapters/telegram.py` | Telegram Bot API adapter (stub) |
| `adapters/rest_api.py` | REST API pass-through adapter |

## Inbound Flow

1. Webhook hits `/api/v1/communication/webhooks/{channel}`
2. Channel adapter normalizes raw payload → `NormalizedInboundEvent`
3. `CommunicationService.process_inbound()`:
   - Dedup check (idempotency_key)
   - Resolve/create `ChannelIdentity`
   - Find/create `Conversation`
   - Persist `Message`

## Outbound Flow

1. Kernel produces an `OutboundMessage`
2. `dispatcher.dispatch_message()` routes to the correct adapter
3. Adapter sends via channel API, returns `DeliveryReceipt`
4. Receipt stored as `MessageEvent`
