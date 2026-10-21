# DevWatch audit remediation

This branch implements a focused subset of the read-only Grok audit. It does not complete all LifeOS automation work.

## Implemented in this branch

- Paginated collection reads for workflow runs and open pull requests (bounded to 10 pages).
- Modern GitHub check-runs API failures, alongside the combined commit-status API.
- Bounded retries for rate-limit responses when GitHub provides Retry-After or a primary rate-limit reset.
- Incident fingerprints normalize URLs so a changed run URL does not generate the same alert every night.
- DevWatch persists the new state only after Telegram delivery succeeds; a failed alert leaves old state in place so the next run can retry.
- Optional expected_text site checks detect soft-404 pages with HTTP 200 responses.
- Selfcheck now runs when regression tests change.

## Still open from the audit

- Live scheduled run and Telegram delivery are not verified by offline CI.
- TLS certificate expiry monitoring and deeper page-content checks are not implemented.
- GitHub Actions disabled-at-organization-level detection is not yet explicit.
- Private repository visibility still depends on a suitable GH_PAT; no secret scopes can be verified offline.
- State writes are serialized by the existing workflow concurrency group, but the rebase/push pattern has not been stress-tested with concurrent writers.
- Retry handling for Telegram 429/network failures is not yet a durable outbox; it only prevents the incident state from being marked delivered when tg() raises.
- Cloudflare Worker daily jobs, study-task carryover, spaced-revision loops, and weekly review remain separate incomplete work.
- JEE schedule source confirmation and approval-first PDF live test remain open.

## Validation

Offline regression tests cover pagination, check-runs failures, soft-404 content, incident URL deduplication, and retrying alerts after Telegram failure. A passing workflow does not prove live GitHub permissions, scheduled execution, or Telegram delivery.
