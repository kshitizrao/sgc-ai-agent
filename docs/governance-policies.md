# Governance Policies

## Input Guardrails
- Prompt injection detection
- PII redaction in logs

## Output Guardrails
- Tone blocklist (no aggressive upselling, profanity)
- Fact-check: amounts in response must match tool output

## Human-in-the-Loop
- RSA High severity → flag for advisor
- Claim rejection → escalation template

## Audit
All governance events logged to `governance.guardrail_events`.

## Prompt Registry
System prompts versioned in `governance.prompt_versions`. Default in code for v1.
