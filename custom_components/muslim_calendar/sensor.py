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
# CAPTEUR IMSAK
# =============================================================================

class MuslimCalendarImsakSensor(MuslimCalendarSensor):
    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="special_imsak",
            name="Imsak",
            icon="mdi:clock-alert-outline",
            key_path="special/imsak",
        )


# =============================================================================
# CAPTEUR TAHALLUL (Dernier tiers de la nuit)
# =============================================================================

class MuslimCalendarTahajudSensor(MuslimCalendarSensor):
    """Capteur Tahajud (dernier tiers de la nuit = 2/3 entre Isha et Fajr)."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="special_tahajud",
            name="Tahajud",
            icon="mdi:weather-night",
            key_path="special/tahajud",
        )


# =============================================================================
# CAPTEUR DATE HIJRI (UN SEUL CAPTEUR, 5 ATTRIBUTS)
# =============================================================================

class MuslimCalendarDateSensor(MuslimCalendarSensor):
    """State = date complete. Attributes: hijri_day, hijri_month, hijri_month_full, hijri_year, hijri_date_full."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="hijri_date",
            name="Date Hijri",
            icon="mdi:calendar",
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
# CAPTEUR MOIS PROCHAIN (state = date du debut du prochain mois)
# =============================================================================

class MuslimCalendarNextMonthSensor(MuslimCalendarSensor):
    """State = date gregorienne du prochain debut de mois Hijri."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="next_month_start",
            name="Mois Prochain",
            icon="mdi:calendar-month",
        )

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return "Inconnu"
        ms = data.get("next_month")
        if not ms:
            return "Inconnu"
        return ms.get("gregorian", "Inconnu")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        ms = data.get("next_month", {})
        months = data.get("month_starts", [])
        return {
            "next_month_name": ms.get("month_name", ""),
            "next_month_hijri": ms.get("hijri", ""),
            "months": [
                {"name": m.get("month_name", ""), "date": m.get("gregorian", ""), "hijri": m.get("hijri", ""), "month": m.get("month", 0)}
                for m in months
            ],
        }


# =============================================================================
# CAPTEUR EVENEMENTS ISLAMIQUES (attributs par type d'evenement)
# =============================================================================

class MuslimCalendarEventsSensor(MuslimCalendarSensor):
    """State = prochain evenement. Attributes: next_* + event_ par type d'evenement."""

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
        ev_by_type = data.get("event_by_type", {})
        next_ev = data.get("next_event", {})
        events = data.get("all_events", [])

        attrs = {
            "next_event_name": next_ev.get("name", ""),
            "next_event_date": next_ev.get("gregorian", ""),
            "next_event_hijri": next_ev.get("hijri", ""),
            "next_event_arabic": next_ev.get("arabic", ""),
        }

        # Un attribut par type d'evenement (prochaine occurrence)
        for ev_name, ev_data in ev_by_type.items():
            key = ev_name.lower().replace(" ", "_").replace("'", "")
            attrs[f"event_{key}"] = ev_data.get("gregorian", "")

        # Liste complete des 10 evenements
        attrs["events"] = [
            {"name": e.get("name", ""), "date": e.get("gregorian", ""), "hijri": e.get("hijri", ""), "arabic": e.get("arabic", "")}
            for e in events[:10]
        ]

        return attrs


# =============================================================================
# CAPTEUR CRENEAUX INTERDITS (state binaire 0/1 + 6 attributs)
# =============================================================================

class MuslimCalendarForbiddenSensor(MuslimCalendarSensor):
    """State = 1 si dans un slot interdit, 0 sinon. Attributes: 6 slots."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="forbidden_slots",
            name="Creneaux Interdits",
            icon="mdi:cancel",
        )

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return 0
        return data.get("forbidden_now", 0)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        return data.get("forbidden_slots", {})


# =============================================================================
# CAPTEUR CALENDRIER (iCal)
# =============================================================================

class MuslimCalendarCalendarSensor(MuslimCalendarSensor):
    """Capteur calendrier pour Home Assistant Calendar entity."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="calendar",
            name="Calendrier Islamique",
            icon="mdi:calendar",
        )

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return "aucun"
        events = data.get("all_events", [])
        return f"{len(events)} evenements"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        return {
            "events": data.get("calendar_ical", ""),
        }


# =============================================================================
# PLATFORM SETUP
# =============================================================================

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    # Heures de priere
    for idx, (key_path, name, icon) in enumerate(PRAYER_SENSORS):
        suffix = key_path.replace("/", "_")
        entities.append(MuslimCalendarSensor(coordinator, f"prayer_{idx}_{suffix}", name, icon, key_path))

    # Iqamah
    for idx, (key_path, name, icon) in enumerate(IQAMAH_SENSORS):
        suffix = key_path.replace("/", "_")
        entities.append(MuslimCalendarSensor(coordinator, f"iqamah_{idx}_{suffix}", name, icon, key_path))

    # Imsak
    entities.append(MuslimCalendarImsakSensor(coordinator))

    # Tahajud
    entities.append(MuslimCalendarTahajudSensor(coordinator))

    # Date Hijri (un seul capteur)
    entities.append(MuslimCalendarDateSensor(coordinator))

    # Mois Prochain (state = date debut)
    entities.append(MuslimCalendarNextMonthSensor(coordinator))

    # Evenements Islamiques (attributes par type)
    entities.append(MuslimCalendarEventsSensor(coordinator))

    # Creneaux Interdits (state 0/1)
    entities.append(MuslimCalendarForbiddenSensor(coordinator))

    # Calendrier iCal
    entities.append(MuslimCalendarCalendarSensor(coordinator))

    async_add_entities(entities, update_before_add=True)
