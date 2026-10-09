from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseModelAdapter(ABC):
    name: str

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model

    @abstractmethod
    def extract_tasks_and_urgency(self, context_excerpts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Takes task-relevant context excerpts (only relevant snippets from Markdown,
        calendar, or email) and extracts actionable tasks with urgency scores (1-10)
        and explainable rationale.
        """
        pass
