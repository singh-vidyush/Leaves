from typing import Any

from app.integrations.connectors import ScheduleConnector
from .service import (
    add_calendar_event,
    delete_calendar_event,
    list_events,
    move_calendar_event,
    sync_calendar,
    calendar_is_connected,
)


class LocalCalendarConnector:
    """Schedule connector for the current on-device calendar prototype."""

    id = "local_calendar"
    display_name = "Local Calendar"
    @property
    def is_live(self) -> bool:
        return calendar_is_connected()

    def sync(self) -> dict[str, Any]:
        return sync_calendar()

    def list_events(self, limit: int = 50) -> list[dict[str, Any]]:
        return list_events(limit=limit)

    def add_event(
        self, title: str, start_time: str, end_time: str, description: str = ""
    ) -> dict[str, Any]:
        return add_calendar_event(title, start_time, end_time, description)

    def move_event(self, event_id: int, start_time: str, end_time: str) -> dict[str, Any]:
        return move_calendar_event(event_id, start_time, end_time)

    def delete_event(self, event_id: int, *, user_confirmed: bool = False) -> bool:
        return delete_calendar_event(event_id, user_confirmed=user_confirmed)
