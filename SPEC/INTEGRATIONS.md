# Integrations Specification

<!--
Specify how data sources connect to the ingestion pipeline: registration,
permissions, collection, normalization, updates/deletions, errors, and scheduling.
Already established: prioritized sources are user-selected local Markdown,
Gmail, and Google Calendar. Other schedule-bearing apps should be connectable as
well. The user decides what is collected and can delete their Leaves-held data.
Leaves-held data, database, and indexes stay on-device. Selected task context
(relevant email, calendar, or Markdown excerpts) may be sent to the user's
configured cloud model provider (one active provider/model in settings; no automatic
routing). Model requests include only emails identified as relevant to a task, rather
than sending the entire inbox. When a user deletes something from Leaves, only Leaves'
local copy and index are removed, leaving the original email, file, or calendar event untouched.

Recommended Markdown flow: let the user add a folder with the native folder picker,
show the selected folders and indexing status, and let them remove a folder from
Leaves. Scan that selected folder recursively by default, with an option to limit
scanning to its top level. This keeps collection explicit and familiar for a desktop app.

Prioritized connected providers: Gmail and Google Calendar. Gmail is scanned in
full by default, with an option to limit collection by label. The user is open to
connecting other schedule-bearing apps supported by Leaves, but the first release
focuses strictly on understanding tasks and scheduling them. Keep provider
credentials and collected content local; the user accepts authenticating directly
with connected providers. Store API keys and integration tokens in the operating
system's secure credential store where available. Never put secrets in the ordinary
database or logs. Model requests may transmit relevant source excerpts to the
selected provider (one active provider in settings).

Owner decisions confirmed: automatic event additions and moves are authorized, but
deleting calendar events always requires user approval. Deletion of sources/records
removes only Leaves' local copy and index, leaving original items untouched. Working
hours, breaks, and task duration defaults will be configurable and decided later.
Accepted Markdown extensions, refresh cadence, and minimum account permissions remain
to be refined during implementation.
-->

<!-- Define the provider connection lifecycle, permissions, sync, and schedule
write rules after the remaining owner decisions are answered. -->
