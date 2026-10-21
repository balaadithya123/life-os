# Schedule intake agent

1. Upload the source PDF to inbox/schedules/ and commit it, or manually run Actions → schedule-intake → Run workflow on the branch containing the PDF.
2. The workflow extracts selectable PDF text and generates state/schedule_proposal.md and state/schedule_proposal.json.
3. It compares extracted daily chapter rows and test events with config/plan.yml and config/tests.yml, then flags detected conflicts.
4. Telegram receives a concise notification asking the owner to review the proposal.

## Safety guarantees
- The importer never edits config/plan.yml or config/tests.yml.
- It never applies proposed changes automatically. Explicit owner approval of the exact changes is required.
- PDFs without selectable text are rejected; OCR is not silently attempted.
- Parsing is conservative. Review source lines, warnings, and conflicts in every proposal.
- The workflow is event/manual-driven, not hourly, to avoid duplicating existing daily Telegram messages.

## Known limitations
- Merged PDF table columns, scanned pages, and dates split across lines can be missed or classified as warnings.
- Automated conflict detection covers no QPT on AITS Main Sundays and at most one QPT in Cycle 7; human review is still required.
- Telegram delivery is required for a successful run; a failed send fails the workflow.
