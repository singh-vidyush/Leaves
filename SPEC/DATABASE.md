# Database Specification

<!--
Document the SQLite schema, relationships, indexes, migrations, and vector storage.
Recommended first-release choice: SQLite with FTS5 for source metadata and indexed
Markdown text. FTS5 is SQLite's built-in full-text search module. This avoids adding
a separate vector database or vector extension before semantic search is confirmed
as a first-release requirement. See https://www.sqlite.org/fts5.html.

Owner decisions confirmed: deleting something from Leaves removes only Leaves'
local copy and index, leaving the original email, file, or calendar event untouched.
Owner input still needed: whether indexed content is a copy or derived cache of the
source files, exact entities and fields, export format, migration approach, and encryption/backup
requirements. Provider API keys and integration tokens must be kept outside the
ordinary content database in the operating system's secure credential store where
available. Persist agent decisions/actions with source provenance so the user can
inspect, export, and delete Leaves-held records. Do not persist provider request
payloads by default unless the owner explicitly chooses a history feature.
-->

<!-- Python's standard sqlite3 module can access SQLite without requiring a separate
database server process. https://docs.python.org/3/library/sqlite3.html -->
