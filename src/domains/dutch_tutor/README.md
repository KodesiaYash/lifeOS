# Dutch Tutor Domain

The `dutch_tutor` domain is the first promoted conversational domain in AI Life OS.

## Current capability

- Telegram and REST entrypoints route into the platform communication pipeline.
- The global orchestrator resolves the `dutch_tutor` domain and retrieves:
  - shared `general` memory for durable learner profile facts
  - `dutch_tutor` memory for Dutch-learning-specific facts
- A deterministic translation tool handles the MVP use case:
  - translate a single Dutch or English word
  - show Dutch -> English -> Dutch roundtrip output

## Memory split

General memory stores durable cross-domain facts such as:
- learner name
- native language
- preferred explanation language

Domain memory stores Dutch-only tutoring facts such as:
- CEFR level
- focus area (grammar, vocabulary, speaking, writing, listening, pronunciation)
- exam target (KNM, inburgering, NT2)
- correction style

## Local validation

- `POST /api/v1/domains/dutch_tutor/translate`
- Send a word like `huis` and expect `house` plus the Dutch roundtrip.
