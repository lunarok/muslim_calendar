"""
Muslim Calendar - Capteurs Home Assistant.
Un device avec 1 entite par information.
"""

import logging
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, DEVICE_NAME, HIJRI_MONTHS_FR
from . import MuslimCalendarDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# CAPTEUR SALAT DE BASE
# =============================================================================

class MuslimCalendarSensor(Entity):
    """Capteur generique."""

    def __init__(
        self,
        coordinator: MuslimCalendarDataUpdateCoordinator,
        unique_id_suffix: str,
        name: str,
        icon: str,
        key_path: str = None,
    ):
        self.coordinator = coordinator
        self._key_path = key_path or unique_id_suffix
        self._attr_unique_id = f"{DOMAIN}_{unique_id_suffix}"
        self._attr_name = name
        self._attr_icon = icon
        self._attr_device_info = coordinator._get_device_info()

    def _get_nested(self, data, key_path: str):
        if not data or not key_path:
            return None
        parts = key_path.split("/")
        value = data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return None
        value = self._get_nested(data, self._key_path)
        return value if value is not None else "Inconnu"

    async def async_update(self):
        await self.coordinator.async_request_refresh()


# =============================================================================
# CAPTEURS HORAIRES DE PRIERE
# =============================================================================

PRAYER_SENSORS = [
    ("prayer_times/fajr", "Fajr", "mdi:weather-sunset-up"),
    ("prayer_times/shuruq", "Shuruq", "mdi:weather-sunset"),
    ("prayer_times/dhuhr", "Dhuhr", "mdi:weather-sunny"),
    ("prayer_times/asr", "Asr", "mdi:weather-sunset-down"),
    ("prayer_times/maghrib", "Maghrib", "mdi:weather-night"),
    ("prayer_times/isha", "Isha", "mdi:weather-night"),
    ("prayer_times/midnight", "Minuit", "mdi:weather-night"),
]

IQAMAH_SENSORS = [
    ("iqamah_times/fajr", "Iqamah Fajr", "mdi:clock-check-outline"),
    ("iqamah_times/dhuhr", "Iqamah Dhuhr", "mdi:clock-check-outline"),
    ("iqamah_times/asr", "Iqamah Asr", "mdi:clock-check-outline"),
    ("iqamah_times/maghrib", "Iqamah Maghrib", "mdi:clock-check-outline"),
    ("iqamah_times/isha", "Iqamah Isha", "mdi:clock-check-outline"),
]


# =============================================================================
# CAPTEUR IMSAK (10 min avant Fajr)
# =============================================================================

class MuslimCalendarImsakSensor(MuslimCalendarSensor):
    """Capteur Imsak."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="special_imsak",
            name="Imsak",
            icon="mdi:clock-alert-outline",
            key_path="special/imsak",
        )


# =============================================================================
# CAPTEUR DATE HIJRI (UN SEUL CAPTEUR AVEC ATTRIBUTS)
# =============================================================================

class MuslimCalendarDateSensor(MuslimCalendarSensor):
    """Capteur date Hijri.

    state = date complete (ex: "10 Ramadan 1447")
    attributes:
        - hijri_day (int)
        - hijri_month (int)
        - hijri_month_full (str)
        - hijri_year (int)
        - hijri_date_full (str)
    """

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="hijri_date",
            name="Date Hijri",
            icon="mdi:calendar伊斯兰",
            key_path="hijri_date/date_full",
        )

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return "Inconnu"
        hijri = data.get("hijri_info", {})
        if not hijri:
            return "Inconnu"
        month_name = HIJRI_MONTHS_FR.get(hijri.get("month", 0), "?")
        return f"{hijri.get('day', 0)} {month_name} {hijri.get('year', 0)}"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        hijri = data.get("hijri_info", {})
        month_name = HIJRI_MONTHS_FR.get(hijri.get("month", 0), "?")
        return {
            "hijri_day": hijri.get("day", 0),
            "hijri_month": hijri.get("month", 0),
            "hijri_month_full": month_name,
            "hijri_year": hijri.get("year", 0),
            "hijri_date_full": f"{hijri.get('day', 0)} {month_name} {hijri.get('year', 0)}",
        }


# =============================================================================
# CAPTEUR MOIS HIJRI (AVEC ATTRIBUTS)
# =============================================================================

class MuslimCalendarMonthsSensor(MuslimCalendarSensor):
    """Capteur Mois Hijri.

    state = prochain mois
    attributes = {next_*, months: [...]}
    """

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="hijri_months",
            name="Mois Hijri",
            icon="mdi:calendar-month",
        )

    @property
    def state(self):
        data = self.coordinator.data
        if not data or not data.get("next_month"):
            return "Inconnu"
        return data["next_month"].get("month_name", "Inconnu")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        months = data.get("month_starts", [])
        next_month = data.get("next_month", {})
        return {
            "next_month_name": next_month.get("month_name", ""),
            "next_month_date": next_month.get("gregorian", ""),
            "next_month_hijri": next_month.get("hijri", ""),
            "months": [
                {"name": m.get("month_name", ""), "date": m.get("gregorian", ""), "hijri": m.get("hijri", ""), "month": m.get("month", 0)}
                for m in months
            ],
        }


# =============================================================================
# CAPTEUR EVENEMENTS (AVEC ATTRIBUTS)
# =============================================================================

class MuslimCalendarEventsSensor(MuslimCalendarSensor):
    """Capteur Evenements Islamiques.

    state = prochain evenement
    attributes = {next_*, events: [...]}
    """

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="hijri_events",
            name="Evenements Islamiques",
            icon="mdi:star",
        )

    @property
    def state(self):
        data = self.coordinator.data
        if not data or not data.get("next_event"):
            return "Aucun"
        return data["next_event"].get("name", "Aucun")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        events = data.get("all_events", [])
        next_event = data.get("next_event", {})
        return {
            "next_event_name": next_event.get("name", ""),
            "next_event_date": next_event.get("gregorian", ""),
            "next_event_hijri": next_event.get("hijri", ""),
            "next_event_arabic": next_event.get("arabic", ""),
            "events": [
                {"name": e.get("name", ""), "date": e.get("gregorian", ""), "hijri": e.get("hijri", ""), "arabic": e.get("arabic", "")}
                for e in events
            ],
        }


# =============================================================================
# CAPTEUR CRENEAUX INTERDITS (AVEC ATTRIBUTS)
# =============================================================================

class MuslimCalendarForbiddenSensor(MuslimCalendarSensor):
    """Capteur Creneaux Interdits a la priere.

    state = slot1_start
    attributes:
        - slot1_start (shuruq)
        - slot1_end (shuruq + 20 min)
        - slot2_start (zawwal / Dhuhr)
        - slot2_end (zawwal + 20 min)
        - slot3_start (maghrib - 20 min)
        - slot3_end (maghrib)
    """

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="forbidden_slots",
            name="Creneaux interdits",
            icon="mdi:clock-pause",
        )

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return "Inconnu"
        slots = data.get("forbidden_slots", {})
        return slots.get("slot1_start", "Inconnu")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        return data.get("forbidden_slots", {})


# =============================================================================
# PLATFORM SETUP
# =============================================================================

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    # Heures de priere (fajr, shuruq, dhuhr, asr, maghrib, isha, midnight)
    for key_path, name, icon in PRAYER_SENSORS:
        suffix = key_path.replace("/", "_")
        entities.append(MuslimCalendarSensor(coordinator, f"prayer_{suffix}", name, icon, key_path))

    # Iqamah
    for key_path, name, icon in IQAMAH_SENSORS:
        suffix = key_path.replace("/", "_")
        entities.append(MuslimCalendarSensor(coordinator, f"iqamah_{suffix}", name, icon, key_path))

    # Imsak
    entities.append(MuslimCalendarImsakSensor(coordinator))

    # Date Hijri (UN seul capteur avec 5 attributs)
    entities.append(MuslimCalendarDateSensor(coordinator))

    # Mois Hijri avec attributs
    entities.append(MuslimCalendarMonthsSensor(coordinator))

    # Evenements avec attributs
    entities.append(MuslimCalendarEventsSensor(coordinator))

    # Creneaux interdits avec 6 attributs
    entities.append(MuslimCalendarForbiddenSensor(coordinator))

    async_add_entities(entities, update_before_add=True)
