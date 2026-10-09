"""Contract and registry for schedule-bearing integrations.

New providers implement this interface and register an instance below. The
    Google Calendar is used when connected; the local sample calendar remains
    available for preview when no Google account is connected.
"""

from typing import Any, Protocol


class ScheduleConnector(Protocol):
    id: str
    display_name: str
    is_live: bool

    def sync(self) -> dict[str, Any]: ...

    def list_events(self, limit: int = 50) -> list[dict[str, Any]]: ...

    def add_event(
        self, title: str, start_time: str, end_time: str, description: str = ""
    ) -> dict[str, Any]: ...

    def move_event(self, event_id: int, start_time: str, end_time: str) -> dict[str, Any]: ...

    def delete_event(self, event_id: int, *, user_confirmed: bool = False) -> bool: ...


def get_schedule_connectors() -> list[ScheduleConnector]:
    # Import lazily so connector modules can depend on common integration code.
    from app.integrations.google_calendar.connector import LocalCalendarConnector

    return [LocalCalendarConnector()]


def get_schedule_connector(connector_id: str) -> ScheduleConnector:
    for connector in get_schedule_connectors():
        if connector.id == connector_id:
            return connector
    raise LookupError(f"Schedule connector '{connector_id}' is not registered.")
