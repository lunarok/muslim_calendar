"""
Muslim Calendar - Sensor platform.
Cree un device Salat avec 1 entite par information.
"""

import logging
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, DEVICE_NAME
from . import SalatDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# =============================================================================
# DESCRIPTIONS DES CAPTEURS
# =============================================================================

PRAYER_SENSORS = [
    ("prayer_times/fajr", "Fajr", "mdi:weather-sunset-up"),
    ("prayer_times/sunrise", "Lever du soleil", "mdi:weather-sunset"),
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

SPECIAL_SENSORS = [
    ("imsak", "Imsak", "mdi:clock-alert-outline"),
    ("fajr_end", "Fin Fajr", "mdi:clock-end"),
    ("forbidden_start", "Debut creneau interdit", "mdi:clock-pause"),
    ("forbidden_end", "Fin creneau interdit", "mdi:clock-start"),
]


# =============================================================================
# CAPTEUR SALAT
# =============================================================================

class SalatSensor(Entity):
    """Capteur Salat generique."""

    def __init__(
        self,
        coordinator: SalatDataUpdateCoordinator,
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
        """Accede a une cle nestede comme 'prayer_times/fajr' dans data dict."""
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


class SalatSpecialSensor(SalatSensor):
    """Capteur special pour imsak, creneau interdit, etc."""

    def __init__(self, coordinator, unique_id_suffix: str, name: str, icon: str, key_path: str):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix=unique_id_suffix,
            name=name,
            icon=icon,
            key_path=key_path,
        )


class SalatDateSensor(SalatSensor):
    """Capteur date Hijri (jour, mois, annee separes)."""

    def __init__(self, coordinator, unique_id_suffix: str, name: str, icon: str, key_path: str):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix=unique_id_suffix,
            name=name,
            icon=icon,
            key_path=key_path,
        )


class SalatMonthsSensor(SalatSensor):
    """Capteur Mois Hijri - state = prochain mois, attrs = tous les mois."""

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
        if not data:
            return "Inconnu"
        next_month = data.get("next_month")
        if not next_month:
            return "Inconnu"
        return next_month.get("month_name", "Inconnu")

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


class SalatEventsSensor(SalatSensor):
    """Capteur Evenements Hijri - state = prochain evenement, attrs = tous les evenements."""

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
        if not data:
            return "Aucun"
        next_event = data.get("next_event")
        if not next_event:
            return "Aucun"
        return next_event.get("name", "Aucun")

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
# PLATFORM SETUP
# =============================================================================

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    # Heures de priere
    for key_path, name, icon in PRAYER_SENSORS:
        suffix = key_path.replace("/", "_")
        entities.append(SalatSensor(coordinator, f"prayer_{suffix}", name, icon, key_path))

    # Iqamah
    for key_path, name, icon in IQAMAH_SENSORS:
        suffix = key_path.replace("/", "_")
        entities.append(SalatSensor(coordinator, f"iqamah_{suffix}", name, icon, key_path))

    # Speciaux
    for key_path, name, icon in SPECIAL_SENSORS:
        entities.append(SalatSpecialSensor(coordinator, f"special_{key_path}", name, icon, key_path))

    # Dates Hijri
    for date_type in ["day", "month", "year"]:
        entities.append(SalatDateSensor(
            coordinator, f"hijri_{date_type}", f"Jour Hijri".replace("Jour", "Annee" if date_type == "year" else "Mois" if date_type == "month" else "Jour"),
            "mdi:calendar-today", f"hijri_info/{date_type}"
        ))

    # Mois Hijri avec attributs
    entities.append(SalatMonthsSensor(coordinator))

    # Evenements avec attributs
    entities.append(SalatEventsSensor(coordinator))

    async_add_entities(entities, update_before_add=True)
