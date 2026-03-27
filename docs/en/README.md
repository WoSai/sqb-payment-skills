# Shouqianba Payment Skills (English Skeleton)

This is the English skeleton for pilot teams that need bilingual onboarding material.

## Current Scope

- Official reference implementations: **Java / Python**
- Skill output layering: `protocol` / `adapter` / `support` / `bootstrap`
- Modes: full-flow generation and single-module generation

## Pilot Safety Notes

- Shouqianba has no sandbox for trade APIs; test flows can involve real funds.
- Callback verification (`RSA SHA256WithRSA`) and idempotency are mandatory.

## P1 Documents

- [Error Scenario Checklist](../error-scenarios.md)
- [Key Rotation Runbook](../key-rotation-runbook.md)
- [Field Constraints](../field-constraints.md)
- [Generated Code Review Checklist](./generated-code-review-checklist.md)
