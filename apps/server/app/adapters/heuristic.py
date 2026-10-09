import re
from datetime import datetime, timedelta, timezone
from typing import Any

from .base import BaseModelAdapter

TASK_TRIGGERS = [
    re.compile(r"^\s*-\s*\[\s*\]\s+(.*)", re.MULTILINE),  # - [ ] task
    re.compile(r"(?:TODO|FIXME|ACTION REQUIRED|Action Item):\s*(.*)", re.IGNORECASE),
    re.compile(r"(?:please|need to|must|should|have to|plan to)\s+([^\.\n]+)", re.IGNORECASE),
    re.compile(r"follow[\s-]up\s+(?:on|with)?\s*([^\.\n]+)", re.IGNORECASE),
]

URGENT_KEYWORDS = ["asap", "urgent", "today", "immediately", "critical", "blocking", "emergency", "by tomorrow"]
MODERATE_KEYWORDS = ["this week", "review", "due", "deadline", "soon", "prepare", "meeting", "complete"]


class HeuristicExtractor(BaseModelAdapter):
    name = "heuristic"

    def extract_tasks_and_urgency(self, context_excerpts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        extracted: list[dict[str, Any]] = []

        for item in context_excerpts:
            source_type = item.get("source_type", "unknown")
            source_ref = item.get("source_ref", "")
            title_hint = item.get("title", "")
            text = item.get("content", "")

            # Check lines and regexes
            found_titles: set[str] = set()
            for pattern in TASK_TRIGGERS:
                matches = pattern.findall(text)
                for match in matches:
                    clean = match.strip().rstrip(".").strip()
                    if len(clean) >= 4 and len(clean) <= 120 and clean.lower() not in found_titles:
                        found_titles.add(clean.lower())
                        score, reason = self._score_urgency(clean, text)
                        duration = self._estimate_duration(clean)
                        deadline = self._find_deadline(clean, text)

                        extracted.append({
                            "title": clean,
                            "description": f"Extracted from {source_type}: {title_hint or source_ref}",
                            "source_type": source_type,
                            "source_ref": source_ref,
                            "urgency_score": score,
                            "urgency_reason": reason,
                            "suggested_duration_minutes": duration,
                            "deadline": deadline,
                        })

            # If no explicit match but item itself looks like a direct task/request
            if not found_titles and text:
                lower = text.lower()
                if any(w in lower for w in URGENT_KEYWORDS + MODERATE_KEYWORDS):
                    summary = title_hint or text.splitlines()[0][:80]
                    score, reason = self._score_urgency(summary, text)
                    extracted.append({
                        "title": summary,
                        "description": text[:200],
                        "source_type": source_type,
                        "source_ref": source_ref,
                        "urgency_score": score,
                        "urgency_reason": reason,
                        "suggested_duration_minutes": 30,
                        "deadline": self._find_deadline(summary, text),
                    })

        return extracted

    def _score_urgency(self, task_title: str, context: str) -> tuple[int, str]:
        combined = f"{task_title} {context}".lower()
        for kw in URGENT_KEYWORDS:
            if kw in combined:
                return 9, f"Contains urgent keyword '{kw}'"
        for kw in MODERATE_KEYWORDS:
            if kw in combined:
                return 6, f"Contains priority keyword '{kw}'"
        return 4, "Standard priority extracted task"

    def _estimate_duration(self, task_title: str) -> int:
        lower = task_title.lower()
        if "quick" in lower or "call" in lower or "check" in lower or "ping" in lower:
            return 15
        if "review" in lower or "write" in lower or "draft" in lower or "prepare" in lower:
            return 45
        if "design" in lower or "implement" in lower or "build" in lower or "plan" in lower:
            return 60
        return 30

    def _find_deadline(self, task_title: str, context: str) -> str | None:
        combined = f"{task_title} {context}".lower()
        now = datetime.now(timezone.utc)
        if "today" in combined:
            return now.replace(hour=18, minute=0, second=0).isoformat()
        if "tomorrow" in combined:
            return (now + timedelta(days=1)).replace(hour=18, minute=0, second=0).isoformat()
        if "by friday" in combined:
            days_ahead = (4 - now.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return (now + timedelta(days=days_ahead)).replace(hour=17, minute=0, second=0).isoformat()
        return None
