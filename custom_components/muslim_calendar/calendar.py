"""
Calendar platform for Muslim Calendar.
Creates a native Home Assistant Calendar entity with Islamic events.
"""

import logging
from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from . import MuslimCalendarDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Muslim Calendar calendar platform."""
    coordinator: MuslimCalendarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([MuslimCalendarCalendarEntity(coordinator)], True)


class MuslimCalendarCalendarEntity(CalendarEntity):
    """Native Home Assistant Calendar entity for Islamic events."""

    _attr_has_entity_name = True
    _attr_name = "Islamic Events"
    _attr_unique_id = f"{DOMAIN}_calendar"
    _attr_icon = "mdi:calendar"

    def __init__(self, coordinator: MuslimCalendarDataUpdateCoordinator):
        self.coordinator = coordinator

    @property
    def device_info(self):
        return self.coordinator._get_device_info()

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        data = self.coordinator.data
        if not data:
            return None
        next_ev = data.get("next_event")
        if not next_ev:
            return None
        try:
            event_date = datetime.strptime(next_ev.get("gregorian", ""), "%Y-%m-%d").date()
            return CalendarEvent(
                summary=next_ev.get("name", ""),
                start=event_date,
                end=event_date,
                description=next_ev.get("arabic", ""),
                uid=next_ev.get("hijri", ""),
            )
        except (ValueError, TypeError):
            return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Get all events in a specific time frame."""
        data = self.coordinator.data
        if not data:
            return []
        all_events = data.get("all_events", [])
        month_starts = data.get("month_starts", [])
        events = []

        # Add Islamic events
        for ev in all_events:
            try:
                event_date = datetime.strptime(ev.get("gregorian", ""), "%Y-%m-%d").date()
                if start_date.date() <= event_date <= end_date.date():
                    events.append(CalendarEvent(
                        summary=ev.get("name", ""),
                        start=event_date,
                        end=event_date,
                        description=ev.get("arabic", ""),
                        uid=f"event_{ev.get('hijri', '')}",
                    ))
            except (ValueError, TypeError):
                pass

        # Add month starts
        for ms in month_starts:
            try:
                ms_date = datetime.strptime(ms.get("gregorian", ""), "%Y-%m-%d").date()
                if start_date.date() <= ms_date <= end_date.date():
                    events.append(CalendarEvent(
                        summary=f"Start of {ms.get('month_name', '')}",
                        start=ms_date,
                        end=ms_date,
                        description="",
                        uid=f"month_{ms.get('hijri', '')}",
                    ))
            except (ValueError, TypeError):
                pass

        return events

    async def async_update(self) -> None:
        """Update entity state."""
        await self.coordinator.async_request_refresh()
