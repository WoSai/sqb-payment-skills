# Generated Code Review Checklist (English Skeleton)

Use this checklist to review AI-generated Shouqianba integration code before pilot rollout.

## Architecture
- [ ] Layering is clear: `protocol / adapter / support / bootstrap`
- [ ] Provider-specific fields are isolated from core business domain

## Payment Correctness
- [ ] Three-layer status parsing is present
- [ ] Non-final states are handled by polling/query fallback
- [ ] `client_sn` uniqueness is guaranteed

## Security
- [ ] Shared signing utility is reused (no duplicate inline signing)
- [ ] Callback signature verification is mandatory (`RSA SHA256WithRSA`)
- [ ] Invalid signature requests are rejected

## Idempotency & Compensation
- [ ] Notify handlers deduplicate by `sn` or `client_sn`
- [ ] Duplicate callbacks do not trigger duplicate side effects
- [ ] Timeout paths have explicit manual fallback

## Operations
- [ ] No-sandbox warning is explicitly documented
- [ ] Logging fields include `client_sn`, `terminal_sn`, status, and error code
