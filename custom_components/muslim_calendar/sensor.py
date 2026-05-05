"""
Muslim Calendar - Sensors for Home Assistant.
One device with entities for prayer times, hijri date, events, and forbidden slots.
"""

import logging
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, HIJRI_MONTHS_EN, HIJRI_MONTH_KEYS
from . import MuslimCalendarDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# PRAYER TIMES (without Midnight)
# =============================================================================

PRAYER_SENSORS = [
    ("prayer_times/fajr", "Fajr", "mdi:weather-sunset-up"),
    ("prayer_times/shuruq", "Shuruq", "mdi:weather-sunset"),
    ("prayer_times/dhuhr", "Dhuhr", "mdi:weather-sunny"),
    ("prayer_times/asr", "Asr", "mdi:weather-sunset-down"),
    ("prayer_times/maghrib", "Maghrib", "mdi:weather-night"),
    ("prayer_times/isha", "Isha", "mdi:weather-night"),
]

# Iqamah (defined here but created in setup with separate keys)
IQAMAH_DEFS = [
    ("Iqamah Fajr", "fajr"),
    ("Iqamah Dhuhr", "dhuhr"),
    ("Iqamah Asr", "asr"),
    ("Iqamah Maghrib", "maghrib"),
    ("Iqamah Isha", "isha"),
]


# =============================================================================
# BASE SENSOR CLASS
# =============================================================================

class MuslimCalendarSensor(Entity):
    """Base sensor class."""

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
        if value is None:
            return "Unknown"
        # Convert "HH:MM" to ISO timestamp with timezone offset for time trigger compatibility
        if isinstance(value, str) and len(value) == 5 and value[2] == ":":
            from datetime import datetime
            from zoneinfo import ZoneInfo
            tz_name = str(self.coordinator.hass.config.time_zone) if self.coordinator.hass.config.time_zone else "UTC"
            tz = ZoneInfo(tz_name)
            today = datetime.now(tz).date().isoformat()
            dt = datetime.strptime(f"{today} {value}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)
            return dt.isoformat()
        return value

    async def async_update(self):
        await self.coordinator.async_request_refresh()


# =============================================================================
# IMSAK SENSOR
# =============================================================================

class MuslimCalendarImsakSensor(MuslimCalendarSensor):
    """Imsak time (10 minutes before Fajr)."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="special_imsak",
            name="Imsak",
            icon="mdi:clock-alert-outline",
            key_path="special/imsak",
        )
        self._attr_device_class = "timestamp"


# =============================================================================
# TAHADJUD SENSOR
# =============================================================================

class MuslimCalendarTahajudSensor(MuslimCalendarSensor):
    """Tahajjud time (last third of night)."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="special_tahajud",
            name="Tahajjud",
            icon="mdi:weather-night",
            key_path="special/tahajud",
        )
        self._attr_device_class = "timestamp"


# =============================================================================
# HIJRI DATE SENSOR
# =============================================================================

class MuslimCalendarDateSensor(MuslimCalendarSensor):
    """Hijri date sensor with 5 attributes."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="hijri_date",
            name="Hijri Date",
            icon="mdi:calendar",
            key_path="hijri_date/date_full",
        )

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return "Unknown"
        hijri = data.get("hijri_info", {})
        if not hijri:
            return "Unknown"
        month_name = HIJRI_MONTHS_EN.get(hijri.get("month", 0), "?")
        return f"{hijri.get('day', 0)} {month_name} {hijri.get('year', 0)}"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        hijri = data.get("hijri_info", {})
        month_name = HIJRI_MONTHS_EN.get(hijri.get("month", 0), "?")
        return {
            "hijri_day": hijri.get("day", 0),
            "hijri_month": hijri.get("month", 0),
            "hijri_month_full": month_name,
            "hijri_year": hijri.get("year", 0),
            "hijri_date_full": f"{hijri.get('day', 0)} {month_name} {hijri.get('year', 0)}",
        }


# =============================================================================
# TOMORROW HIJRI DATE SENSOR
# =============================================================================

class MuslimCalendarTomorrowHijriSensor(MuslimCalendarSensor):
    """Tomorrow's Hijri date sensor with 5 attributes."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="tomorrow_hijri_date",
            name="Tomorrow Hijri Date",
            icon="mdi:calendar",
        )

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return "Unknown"
        hijri = data.get("tomorrow_hijri_info", {})
        if not hijri:
            return "Unknown"
        month_name = HIJRI_MONTHS_EN.get(hijri.get("month", 0), "?")
        return f"{hijri.get('day', 0)} {month_name} {hijri.get('year', 0)}"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        hijri = data.get("tomorrow_hijri_info", {})
        month_name = HIJRI_MONTHS_EN.get(hijri.get("month", 0), "?")
        return {
            "hijri_day": hijri.get("day", 0),
            "hijri_month": hijri.get("month", 0),
            "hijri_month_full": month_name,
            "hijri_year": hijri.get("year", 0),
            "hijri_date_full": f"{hijri.get('day', 0)} {month_name} {hijri.get('year', 0)}",
        }


# =============================================================================
# NEXT MONTHS SENSOR
# =============================================================================

class MuslimCalendarNextMonthsSensor(MuslimCalendarSensor):
    """Next Hijri months with start dates."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="next_months",
            name="Next Months",
            icon="mdi:calendar-month",
        )

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return "Unknown"
        ms = data.get("next_month")
        if not ms:
            return "Unknown"
        return ms.get("month_name", "Unknown")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        ms = data.get("next_month", {})
        months = data.get("month_starts", [])
        attrs = {
            "next_month_name": ms.get("month_name", ""),
        }
        # Add month_muharram, month_safar, etc.
        for m in months:
            month_num = m.get("month", 0)
            key = HIJRI_MONTH_KEYS.get(month_num, f"month_{month_num}")
            attrs[f"month_{key}"] = m.get("gregorian", "")
        return attrs


# =============================================================================
# EVENTS SENSOR
# =============================================================================

class MuslimCalendarEventsSensor(MuslimCalendarSensor):
    """Islamic events sensor with per-type attributes."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="events",
            name="Events",
            icon="mdi:star",
        )

    @property
    def state(self):
        data = self.coordinator.data
        if not data or not data.get("next_event"):
            return "None"
        return data["next_event"].get("name", "None")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        ev_by_type = data.get("event_by_type", {})
        next_ev = data.get("next_event", {})
        attrs = {
            "next_event_name": next_ev.get("name", ""),
            "next_event_date": next_ev.get("gregorian", ""),
            "next_event_hijri": next_ev.get("hijri", ""),
            "next_event_arabic": next_ev.get("arabic", ""),
        }
        # One attribute per event type
        for ev_name, ev_data in ev_by_type.items():
            key = ev_name.lower().replace(" ", "_").replace("'", "")
            attrs[f"event_{key}"] = ev_data.get("gregorian", "")
        return attrs


# =============================================================================
# MAKRUH IBADAH SENSOR (Forbidden slots)
# =============================================================================

class MuslimCalendarForbiddenSensor(MuslimCalendarSensor):
    """Forbidden prayer slots (makruh times). State = 1 if currently in a forbidden slot."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="makruh_ibadah",
            name="Makruh Ibadah",
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
# NEXT PRAYER SENSOR
# =============================================================================

class MuslimCalendarNextPrayerSensor(MuslimCalendarSensor):
    """Next prayer name, time, and minutes until."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="next_prayer",
            name="Next Prayer",
            icon="mdi:weather-sunny",
        )

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return "Unknown"
        next_p = data.get("next_prayer", {})
        return next_p.get("name", "Unknown")

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        next_p = data.get("next_prayer", {})
        return {
            "next_prayer_name": next_p.get("name", ""),
            "next_prayer_time": next_p.get("time", ""),
            "next_prayer_minutes_until": next_p.get("minutes_until", 0),
            "next_prayer_iqamah": next_p.get("iqamah", ""),
        }


# =============================================================================
# NEXT PRAYER TIME SENSOR
# =============================================================================

class MuslimCalendarNextPrayerTimeSensor(MuslimCalendarSensor):
    """Time of next prayer (state = time string)."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="next_prayer_time",
            name="Next Prayer Time",
            icon="mdi:clock-outline",
        )

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return "Unknown"
        next_p = data.get("next_prayer", {})
        return next_p.get("time", "Unknown")


# =============================================================================
# TOMORROW IMSAK SENSOR
# =============================================================================

class MuslimCalendarTomorrowImsakSensor(MuslimCalendarSensor):
    """Tomorrow's Imsak time (Fajr of next day - 10 min)."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="tomorrow_imsak",
            name="Tomorrow Imsak",
            icon="mdi:clock-alert-outline",
        )
        self._attr_device_class = "timestamp"

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return "Unknown"
        val = data.get("tomorrow_imsak", "Unknown")
        if isinstance(val, str) and len(val) == 5 and val[2] == ":":
            from datetime import datetime
            from zoneinfo import ZoneInfo
            tz_name = str(self.coordinator.hass.config.time_zone) if self.coordinator.hass.config.time_zone else "UTC"
            tz = ZoneInfo(tz_name)
            tomorrow = (datetime.now(tz).date()).isoformat()
            dt = datetime.strptime(f"{tomorrow} {val}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)
            return dt.isoformat()
        return val


# =============================================================================
# TOMORROW PRAYERS SENSOR
# =============================================================================

class MuslimCalendarTomorrowPrayersSensor(MuslimCalendarSensor):
    """Tomorrow's 5 mandatory prayer times."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="tomorrow_prayers",
            name="Tomorrow Prayers",
            icon="mdi:clock-alert-outline",
        )
        self._attr_device_class = "timestamp"

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return "Unknown"
        tp = data.get("tomorrow_prayers", {})
        fajr = tp.get("fajr", "Unknown")
        if isinstance(fajr, str) and len(fajr) == 5 and fajr[2] == ":":
            from datetime import datetime
            from zoneinfo import ZoneInfo
            tz_name = str(self.coordinator.hass.config.time_zone) if self.coordinator.hass.config.time_zone else "UTC"
            tz = ZoneInfo(tz_name)
            tomorrow = (datetime.now(tz).date()).isoformat()
            dt = datetime.strptime(f"{tomorrow} {fajr}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)
            return dt.isoformat()
        return fajr

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        tp = data.get("tomorrow_prayers", {})
        def fmt(v):
            if isinstance(v, str) and len(v) == 5 and v[2] == ":":
                from datetime import datetime
                from zoneinfo import ZoneInfo
                tz_name = str(self.coordinator.hass.config.time_zone) if self.coordinator.hass.config.time_zone else "UTC"
                tz = ZoneInfo(tz_name)
                tomorrow = (datetime.now(tz).date()).isoformat()
                dt = datetime.strptime(f"{tomorrow} {v}", "%Y-%m-%d %H:%M").replace(tzinfo=tz)
                return dt.isoformat()
            return v or ""
        return {
            "Fajr": fmt(tp.get("fajr", "")),
            "Dhuhr": fmt(tp.get("dhuhr", "")),
            "Asr": fmt(tp.get("asr", "")),
            "Maghrib": fmt(tp.get("maghrib", "")),
            "Isha": fmt(tp.get("isha", "")),
        }


# =============================================================================
# PLATFORM SETUP
# =============================================================================

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    # Prayer times (6, no Midnight) — device_class: timestamp
    for idx, (key_path, name, icon) in enumerate(PRAYER_SENSORS):
        suffix = key_path.replace("/", "_")
        sensor = MuslimCalendarSensor(coordinator, f"prayer_{idx}_{suffix}", name, icon, key_path)
        sensor._attr_device_class = "timestamp"
        entities.append(sensor)

    # Iqamah (5 separate entities) — device_class: timestamp
    for idx, (name, suffix) in enumerate([
        ("Iqamah Fajr", "fajr"),
        ("Iqamah Dhuhr", "dhuhr"),
        ("Iqamah Asr", "asr"),
        ("Iqamah Maghrib", "maghrib"),
        ("Iqamah Isha", "isha"),
    ]):
        sensor = MuslimCalendarSensor(
            coordinator,
            f"iqamah_{idx}_{suffix}",
            name,
            "mdi:clock-check-outline",
            f"iqamah_times/iqamah_{suffix}",
        )
        sensor._attr_device_class = "timestamp"
        entities.append(sensor)

    # Imsak
    entities.append(MuslimCalendarImsakSensor(coordinator))

    # Tahajjud
    entities.append(MuslimCalendarTahajudSensor(coordinator))

    # Next Prayer
    entities.append(MuslimCalendarNextPrayerSensor(coordinator))

    # Next Prayer Time
    entities.append(MuslimCalendarNextPrayerTimeSensor(coordinator))

    # Tomorrow Imsak
    entities.append(MuslimCalendarTomorrowImsakSensor(coordinator))

    # Tomorrow Prayers
    entities.append(MuslimCalendarTomorrowPrayersSensor(coordinator))

    # Hijri Date
    entities.append(MuslimCalendarDateSensor(coordinator))

    # Tomorrow Hijri Date
    entities.append(MuslimCalendarTomorrowHijriSensor(coordinator))

    # Next Months
    entities.append(MuslimCalendarNextMonthsSensor(coordinator))

    # Events
    entities.append(MuslimCalendarEventsSensor(coordinator))

    # Makruh Ibadah
    entities.append(MuslimCalendarForbiddenSensor(coordinator))

    # Qibla direction
    entities.append(MuslimCalendarQiblaSensor(coordinator))

    async_add_entities(entities, update_before_add=True)


# =============================================================================
# QIBLA DIRECTION SENSOR
# =============================================================================

class MuslimCalendarQiblaSensor(MuslimCalendarSensor):
    """Qibla direction in degrees from North."""

    def __init__(self, coordinator):
        super().__init__(
            coordinator=coordinator,
            unique_id_suffix="qibla_direction",
            name="Qibla Direction",
            icon="mdi:compass",
        )

    @property
    def state(self):
        data = self.coordinator.data
        if not data:
            return "0"
        return f"{data.get('qibla_direction', 0):.1f}"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if not data:
            return {}
        direction = data.get("qibla_direction", 0)
        return {
            "qibla_degrees": round(direction, 1),
            "qibla_cardinal": self._degrees_to_cardinal(direction),
        }

    def _degrees_to_cardinal(self, degrees: float) -> str:
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                      "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        idx = round(degrees / 22.5) % 16
        return directions[idx]
