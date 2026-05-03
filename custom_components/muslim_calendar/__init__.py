"""
Muslim Calendar - Integration Home Assistant pour les heures de priere islamiques et le calendrier Hijri.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    DEVICE_NAME,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEFAULT_LOCATION,
    CALC_METHODS,
    HIJRI_MONTHS_FR,
    HIJRI_MONTHS_EN,
    HIJRI_MONTH_KEYS,
    ISLAMIC_EVENTS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure l'integration via l'UI Home Assistant."""
    coordinator = MuslimCalendarDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "calendar"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Supprime l'integration."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, ["sensor"]):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


# =============================================================================
# COORDINATOR
# =============================================================================

class MuslimCalendarDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordonne les donnees Muslim Calendar (mise a jour toutes les heures)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.entry = entry
        self._config = entry.data
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=1),
        )

    @property
    def config(self) -> Dict:
        return self._config

    def _get_device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{DOMAIN}_{self._config.get('location', 'custom')}")},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
            entry_type=DeviceEntryType.SERVICE,
        )

    async def _async_update_data(self):
        """Recalcule toutes les donnees."""
        today = date.today()

        lat = self._config.get("lat", DEFAULT_LOCATION["lat"])
        lon = self._config.get("lon", DEFAULT_LOCATION["lon"])
        calc_method = self._config.get("method", "isna")
        adjustments = {
            "Fajr": self._config.get("adjust_fajr", 0),
            "Dhuhr": self._config.get("adjust_dhuhr", 0),
            "Asr": self._config.get("adjust_asr", 0),
            "Maghrib": self._config.get("adjust_maghrib", 0),
            "Isha": self._config.get("adjust_isha", 0),
        }
        iqamah_offsets = {
            "Fajr": self._config.get("iqamah_fajr", 20),
            "Dhuhr": self._config.get("iqamah_dhuhr", 15),
            "Asr": self._config.get("iqamah_asr", 15),
            "Maghrib": self._config.get("iqamah_maghrib", 10),
            "Isha": self._config.get("iqamah_isha", 15),
        }

        # Heures de priere
        prayer_times = await self.hass.async_add_executor_job(
            _calculate_prayer_times, lat, lon, calc_method, adjustments, today
        )

        # Iqamah
        iqamah_times = _calculate_iqamah(prayer_times, iqamah_offsets)

        # Imsak (10 minutes avant Fajr)
        imsak_time = _add_minutes(prayer_times.get("fajr", "--:--"), -10)

        # Tahajud (dernier tiers de la nuit = 2/3 entre Isha et Fajr lendemain)
        tahajud_time = _calculate_tahajud(
            prayer_times.get("isha", INVALID_TIME),
            prayer_times.get("fajr", INVALID_TIME)
        )

        # Creneaux interdits (3 slots) + etat binaire
        shuruq = prayer_times.get("shuruq", INVALID_TIME)
        maghrib = prayer_times.get("maghrib", INVALID_TIME)
        dhuhr = prayer_times.get("dhuhr", INVALID_TIME)
        forbidden_now = _is_in_forbidden_slot(shuruq, maghrib, dhuhr)
        forbidden_slots = {
            "tulu_start": shuruq,
            "tulu_end": _add_minutes(shuruq, 20),
            "istiwa_start": dhuhr,
            "istiwa_end": _add_minutes(dhuhr, 20),
            "ghurub_start": _add_minutes(maghrib, -20),
            "ghurub_end": maghrib,
        }

        # Dates Hijri
        hijri_info = _get_hijri_info(today)
        hijri_date_full = f"{hijri_info['day']} {HIJRI_MONTHS_EN.get(hijri_info['month'], '?')} {hijri_info['year']}"
        hijri_info["date_full"] = hijri_date_full

        # Mois Hijri
        month_starts = _find_month_starts(today, 12)
        next_month = month_starts[0] if month_starts else None

        # Evenements - avec attribut par type d'evenement (10 types)
        all_events = _find_events(today, 365)  # chercher sur 1 an
        event_by_type = _build_event_index(all_events)
        next_event = all_events[0] if all_events else None

        # Calendrier iCal pour Home Assistant Calendar
        calendar_ical = _build_icalendar(next_event, all_events, month_starts)

        return {
            "prayer_times": prayer_times,
            "iqamah_times": iqamah_times,
            "special": {
                "imsak": imsak_time,
                "tahajud": tahajud_time,
            },
            "forbidden_now": 1 if forbidden_now else 0,
            "forbidden_slots": forbidden_slots,
            "hijri_date": hijri_info,
            "hijri_info": hijri_info,
            "month_starts": month_starts,
            "next_month": next_month,
            "next_month_start": next_month.get("gregorian", "") if next_month else "",
            "all_events": all_events,
            "next_event": next_event,
            "event_by_type": event_by_type,
            "tomorrow_prayer_times": await self.hass.async_add_executor_job(
                _calculate_prayer_times, lat, lon, calc_method, adjustments,
                today + timedelta(days=1)
            ),
        }


# =============================================================================
# CONSTANTES
# =============================================================================

INVALID_TIME = "--:--"

KEY_MAP = {
    "Sunrise": "shuruq",
    "Midnight": "midnight",
}


# =============================================================================
# FONCTIONS DE CALCUL
# =============================================================================

def _add_minutes(time_str: str, minutes: int) -> str:
    if not time_str or time_str == INVALID_TIME:
        return INVALID_TIME
    try:
        parts = time_str.split(":")
        hour, minute = int(parts[0]), int(parts[1])
        total = hour * 60 + minute + minutes
        return f"{(total // 60) % 24:02d}:{total % 60:02d}"
    except Exception:
        return INVALID_TIME


def _time_to_minutes(time_str: str) -> int:
    """Convertit HH:MM en minutes depuis minuit."""
    if not time_str or time_str == INVALID_TIME:
        return 0
    try:
        parts = time_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 0


def _calculate_tahajud(isha: str, fajr_tomorrow: str) -> str:
    """Calcule Tahajud = 2/3 entre Isha et Fajr lendemain."""
    try:
        isha_min = _time_to_minutes(isha)
        # Fajr lendemain = minuit + minutes depuis minuit
        fajr_min = _time_to_minutes(fajr_tomorrow)
        # Si Fajr < Isha, ajouter 24h
        if fajr_min <= isha_min:
            fajr_min += 24 * 60
        # Nuit = Fajr - Isha en minutes
        nuit = fajr_min - isha_min
        # Tahajud = Isha + 2/3 de la nuit
        tahajud = isha_min + int(nuit * 2 / 3)
        hour = (tahajud // 60) % 24
        minute = tahajud % 60
        return f"{hour:02d}:{minute:02d}"
    except Exception:
        return INVALID_TIME


def _is_in_forbidden_slot(shuruq: str, maghrib: str, dhuhr: str) -> bool:
    """Retourne 1 si l'heure actuelle est dans un slot interdit."""
    now = datetime.now()
    now_min = now.hour * 60 + now.minute

    # Slot 1: Shuruq a Shuruq + 20
    s1_start = _time_to_minutes(shuruq)
    s1_end = s1_start + 20

    # Slot 2: Dhuhr a Dhuhr + 20 (zawwal)
    s2_start = _time_to_minutes(dhuhr)
    s2_end = s2_start + 20

    # Slot 3: Maghrib - 20 a Maghrib
    s3_start = _time_to_minutes(maghrib) - 20
    s3_end = _time_to_minutes(maghrib)

    # Gerer le cas ou Maghrib < Shuruq dans la journee (passage a minuit)
    if s3_start < 0:
        s3_start += 24 * 60
        s3_end += 24 * 60

    in_slot1 = s1_start <= now_min < s1_end
    in_slot2 = s2_start <= now_min < s2_end
    in_slot3 = s3_start <= now_min < s3_end

    return in_slot1 or in_slot2 or in_slot3


def _calculate_prayer_times(
    lat: float, lon: float, calc_method: str,
    adjustments: Dict[str, int], target_date
) -> Dict[str, str]:
    try:
        from prayer_times_calculator import PrayerTimesCalculator
        calc = PrayerTimesCalculator(
            latitude=lat, longitude=lon,
            calculation_method=calc_method,
            date=str(target_date),
        )
        raw = calc.fetch_prayer_times()
    except Exception as e:
        _LOGGER.error(f"Prayer times calculation failed: {e}")
        return {}

    result = {}
    for prayer in ["Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha", "Midnight"]:
        key = KEY_MAP.get(prayer, prayer.lower())
        time_str = raw.get(prayer)
        if time_str:
            result[key] = _add_minutes(time_str, adjustments.get(prayer, 0))
        else:
            result[key] = INVALID_TIME
    return result


def _calculate_iqamah(prayer_times: Dict, offsets: Dict) -> Dict[str, str]:
    result = {}
    for prayer in ["fajr", "dhuhr", "asr", "maghrib", "isha"]:
        time = prayer_times.get(prayer, INVALID_TIME)
        offset = offsets.get(prayer.title(), 15)
        result[f"iqamah_{prayer}"] = _add_minutes(time, offset)
    return result


def _get_hijri_info(target_date) -> Dict:
    try:
        import hijridate
        h = hijridate.Gregorian(target_date.year, target_date.month, target_date.day).to_hijri()
        return {"day": h.day, "month": h.month, "year": h.year}
    except Exception:
        return {"day": 1, "month": 1, "year": 1445}


def _find_events(start_date, count: int = 365) -> list:
    events = []
    current = start_date
    for _ in range(400):
        if len(events) >= count:
            break
        try:
            import hijridate
            h = hijridate.Gregorian(current.year, current.month, current.day).to_hijri()
            key = (h.month, h.day)
            if key in ISLAMIC_EVENTS:
                ev = dict(ISLAMIC_EVENTS[key])
                ev["date"] = current.isoformat()
                ev["gregorian"] = current.strftime("%Y-%m-%d")
                ev["hijri"] = f"{h.day:02d}-{h.month:02d}-{h.year}"
                events.append(ev)
            current += timedelta(days=1)
        except Exception:
            current += timedelta(days=1)
    return events


def _build_event_index(events: list) -> dict:
    """Construit un index par type d'evenement avec la prochaine occurrence."""
    index = {}
    for ev in events:
        ev_key = ev.get("name", "")
        if ev_key not in index:
            index[ev_key] = ev
    return index


def _find_month_starts(start_date, count: int = 12) -> list:
    starts = []
    current = start_date
    prev_month = None
    found = 0
    for _ in range(400):
        if found >= count:
            break
        try:
            import hijridate
            h = hijridate.Gregorian(current.year, current.month, current.day).to_hijri()
            if prev_month is not None and h.month != prev_month:
                starts.append({
                    "date": current.isoformat(),
                    "gregorian": current.strftime("%Y-%m-%d"),
                    "month": h.month,
                    "month_name": HIJRI_MONTHS_EN.get(h.month, "?"),
                })
                found += 1
            prev_month = h.month
            current += timedelta(days=1)
        except Exception:
            current += timedelta(days=1)
    return starts


def _build_icalendar(next_event, all_events, month_starts) -> str:
    """Genere un calendrier iCal avec les evenements islamiques et debuts de mois."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Muslim Calendar//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Calendrier Islamique",
    ]

    # Evenements
    for ev in all_events[:50]:
        try:
            lines.append("BEGIN:VEVENT")
            lines.append(f"DTSTART;VALUE=DATE:{ev['gregorian'].replace('-', '')}")
            lines.append(f"SUMMARY:{ev['name']}")
            lines.append(f"DESCRIPTION:{ev.get('arabic', '')}")
            lines.append(f"UID:{ev['hijri']}@muslim-calendar")
            lines.append("END:VEVENT")
        except Exception:
            pass

    # Debuts de mois
    for ms in month_starts[:12]:
        try:
            lines.append("BEGIN:VEVENT")
            lines.append(f"DTSTART;VALUE=DATE:{ms['gregorian'].replace('-', '')}")
            lines.append(f"SUMMARY:Debut {ms['month_name']}")
            lines.append(f"UID:month-{ms['hijri']}@muslim-calendar")
            lines.append("END:VEVENT")
        except Exception:
            pass

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)
