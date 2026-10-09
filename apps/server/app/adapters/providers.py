import json
import logging
from typing import Any, Optional
import httpx

from .base import BaseModelAdapter
from .heuristic import HeuristicExtractor

logger = logging.getLogger("leaves.adapters")

EXTRACTION_SYSTEM_PROMPT = """You are the task extraction engine for Leaves, a local-first personal scheduling assistant.
Your job is to analyze excerpts from Markdown files, emails, and calendar entries and extract actionable tasks.
For each task:
- Extract clear title (max 10 words)
- Extract brief description
- Assign urgency score from 1 (lowest) to 10 (highest/critical)
- Provide explainable urgency_reason (why this score was assigned)
- Estimate duration in minutes (e.g. 15, 30, 45, 60)
- Identify deadline in ISO-8601 if explicitly mentioned, or null.

Respond ONLY with valid JSON array of objects:
[
  {
    "title": "string",
    "description": "string",
    "source_type": "string",
    "source_ref": "string",
    "urgency_score": 7,
    "urgency_reason": "string",
    "suggested_duration_minutes": 30,
    "deadline": "YYYY-MM-DDTHH:MM:SS" or null
  }
]
"""


class OpenAIAdapter(BaseModelAdapter):
    name = "openai"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(api_key, model or "gpt-4o-mini")
        self.fallback = HeuristicExtractor()

    def extract_tasks_and_urgency(self, context_excerpts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.api_key:
            return self.fallback.extract_tasks_and_urgency(context_excerpts)

        user_content = json.dumps(context_excerpts, indent=2)
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                            {"role": "user", "content": f"Context excerpts:\n{user_content}"},
                        ],
                        "response_format": {"type": "json_object"},
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    raw = data["choices"][0]["message"]["content"]
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        return parsed
                    if isinstance(parsed, dict):
                        for val in parsed.values():
                            if isinstance(val, list):
                                return val
        except Exception as error:
            logger.warning(f"OpenAI extraction failed, using heuristic fallback: {error}")

        return self.fallback.extract_tasks_and_urgency(context_excerpts)


class AnthropicAdapter(BaseModelAdapter):
    name = "anthropic"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(api_key, model or "claude-3-5-sonnet-20241022")
        self.fallback = HeuristicExtractor()

    def extract_tasks_and_urgency(self, context_excerpts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.api_key:
            return self.fallback.extract_tasks_and_urgency(context_excerpts)

        user_content = json.dumps(context_excerpts, indent=2)
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 1024,
                        "system": EXTRACTION_SYSTEM_PROMPT,
                        "messages": [
                            {"role": "user", "content": f"Extract tasks from these excerpts and return JSON array:\n{user_content}"}
                        ],
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    raw = data["content"][0]["text"]
                    start = raw.find("[")
                    end = raw.rfind("]")
                    if start != -1 and end != -1:
                        return json.loads(raw[start : end + 1])
        except Exception as error:
            logger.warning(f"Anthropic extraction failed, using heuristic fallback: {error}")

        return self.fallback.extract_tasks_and_urgency(context_excerpts)


class GeminiAdapter(BaseModelAdapter):
    name = "gemini"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(api_key, model or "gemini-1.5-flash")
        self.fallback = HeuristicExtractor()

    def extract_tasks_and_urgency(self, context_excerpts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.api_key:
            return self.fallback.extract_tasks_and_urgency(context_excerpts)

        user_content = json.dumps(context_excerpts, indent=2)
        try:
            with httpx.Client(timeout=15.0) as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
                response = client.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [
                            {
                                "parts": [
                                    {"text": f"{EXTRACTION_SYSTEM_PROMPT}\n\nContext excerpts:\n{user_content}"}
                                ]
                            }
                        ]
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    raw = data["candidates"][0]["content"]["parts"][0]["text"]
                    start = raw.find("[")
                    end = raw.rfind("]")
                    if start != -1 and end != -1:
                        return json.loads(raw[start : end + 1])
        except Exception as error:
            logger.warning(f"Gemini extraction failed, using heuristic fallback: {error}")

        return self.fallback.extract_tasks_and_urgency(context_excerpts)
