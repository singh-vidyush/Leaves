# Model Adapters

<!--
Model-provider adapters belong here. Leaves is an agentic app with no chat UI.
Initial candidates are user-keyed OpenAI, Anthropic Claude, and Google Gemini.
The user chooses one active provider/model at a time in settings; do not route
automatically across providers. Ollama is a later local-provider option.

An adapter must not own scheduling policy or execute calendar actions. It returns
structured analysis with source references/uncertainty for the local orchestrator
to check against permissions and availability. Never log API keys or source payloads.
Permitted payload scope is restricted to task-relevant excerpts (and for Gmail, only
emails identified as relevant to a task, not the entire inbox); database and indexes
stay on-device.
-->
