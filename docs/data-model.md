# Data Model

## Schemas

| Schema | Purpose |
|--------|---------|
| catalog | Parts, fitment, services, pricing |
| operations | Claims, RSA, triage |
| marketplace | Garages, capabilities, scoring |
| diagnostics | Issues, symptoms, predictive |
| agent_meta | Sessions, messages, tool invocations |
| governance | Policies, prompts, audit |
| sync | Import jobs, field mappings |

See `packages/db/src/sgc_db/models/` for SQLAlchemy definitions.
