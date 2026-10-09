# AI Pipeline Specification

<!--
Leaves is an agentic scheduling application without a chat interface. It uses
user-provided API keys for supported cloud model providers (initial candidates:
OpenAI, Anthropic Claude, Google Gemini, and other compatible providers selected
later). The user selects one active provider/model at a time in settings (no automatic
routing across providers). Leaves-held database, indexes, and credentials remain local.
Task-relevant Markdown and email excerpts may be sent to the configured provider for
model inference; calendar event text stays local and only event times constrain
scheduling. For Gmail, requests include only emails identified as relevant to a task,
rather than sending the entire inbox. Ollama may be added as a later local provider.
SQLite FTS5 is the initial text-search approach; vector search is deferred unless
prioritized.

For the first release, Leaves focuses on understanding tasks and scheduling them
(broader actions across connected apps are deferred). The model may identify task
candidates, deadlines, urgency signals, dependencies, and suggested durations from
permitted context. Do not silently invent facts: preserve source references,
confidence/uncertainty, and distinguish extracted facts from estimates. Leaves owns
scheduling rules and validation; check availability, working hours, and conflicts
locally before executing an action. Automatic calendar additions and moves are
authorized, subject to the user's availability constraints, but deleting calendar
events always requires user approval.

Owner input status: Model choice/routing (one active provider in settings), permitted
payload (task-relevant Markdown and email excerpts; no calendar event text), calendar deletion
safeguard (user approval required), and agent scope (task understanding and scheduling
only) are confirmed. Working hours, breaks, and task-duration defaults will be
configurable and decided later. Conflict handling and uncertainty presentation to be
finalized during scheduling implementation.
-->

<!-- Define model tasks and retrieval behavior after extraction and scheduling
workflows are prioritized. -->
