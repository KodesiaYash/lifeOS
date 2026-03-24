# Orchestration Module (`src/orchestration/`)

Workflow engine for multi-step, event-driven workflow execution.

## Contents

| File | Purpose |
|------|---------|
| `models.py` | SQLAlchemy models: WorkflowDefinition, WorkflowExecution, WorkflowStepExecution |
| `schemas.py` | Pydantic schemas, WorkflowStatus/StepType/TriggerType enums |
| `repository.py` | Database access for workflow definitions, executions, and steps |
| `engine.py` | `WorkflowEngine` — step-by-step execution with pause/resume support |

## Step Types

| Type | Description |
|------|-------------|
| `llm_call` | Invoke LLM with a prompt template |
| `tool_call` | Invoke a registered tool |
| `condition` | Branch based on context values |
| `parallel` | Run sub-steps concurrently (planned) |
| `wait_for_input` | Pause workflow and wait for user input |
| `emit_event` | Publish a platform event |
| `store_memory` | Store a fact or semantic memory (planned) |
| `transform` | Map data between steps |

## Trigger Types

- `event` — triggered by a platform event
- `schedule` — triggered by cron/interval
- `manual` — triggered by API call
- `webhook` — triggered by external webhook
