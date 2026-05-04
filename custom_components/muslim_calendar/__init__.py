"""
Muslim Calendar - Integration Home Assistant for Islamic prayer times and Hijri calendar.
"""

import logging
from datetime import date, datetime, timedelta, timezone
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
    HIJRI_MONTHS_EN,
    HIJRI_MONTH_KEYS,
    ISLAMIC_EVENTS,
)

_LOGGER = logging.getLogger(__name__)

INVALID_TIME = "--:--"  # was "--:----" before


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure l'integration via l'UI Home Assistant."""
    coordinator = MuslimCalendarDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "calendar"])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Supprime l'integration."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, ["sensor", "calendar"]):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


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
        calc_method = self._config.get("method", "makkah")
        adjustments = {
            "Fajr": self._config.get("adjust_fajr", 0),
            "Dhuhr": self._config.get("adjust_dhuhr", 0),
            "Asr": self._config.get("adjust_asr", 0),
            "Maghrib": self._config.get("adjust_maghrib", 0),
            "Isha": self._config.get("adjust_isha", 0),
        }
        iqamah_offsets = {
            "Fajr": self._config.get("iqamah_fajr", 10),
            "Dhuhr": self._config.get("iqamah_dhuhr", 10),
            "Asr": self._config.get("iqamah_asr", 10),
            "Maghrib": self._config.get("iqamah_maghrib", 5),
            "Isha": self._config.get("iqamah_isha", 5),
        }
        fajr_angle = self._config.get("fajr_angle")
        isha_angle = self._config.get("isha_angle")

        # Heures de priere
        prayer_times = await self.hass.async_add_executor_job(
            _calculate_prayer_times, lat, lon, calc_method, adjustments, today,
            fajr_angle, isha_angle
        )

        # Iqamah
        iqamah_times = _calculate_iqamah(prayer_times, iqamah_offsets)

        # Imsak (10 minutes avant Fajr)
        imsak_time = _add_minutes(prayer_times.get("fajr", INVALID_TIME), -10)

        # Tahajud (dernier tiers de la nuit = 2/3 entre Isha et Fajr lendemain)
        tahajud_time = _calculate_tahajud(
            prayer_times.get("isha", INVALID_TIME),
            prayer_times.get("fajr", INVALID_TIME)
        )

        # Creneaux interdits (3 slots) + etat binaire
        shuruq = prayer_times.get("shuruq", INVALID_TIME)
        maghrib = prayer_times.get("maghrib", INVALID_TIME)
        dhuhr = prayer_times.get("dhuhr", INVALID_TIME)
        tulu_offset = self._config.get("tulu_offset", 20)
        istiwa_offset = self._config.get("istiwa_offset", 10)
        ghurub_offset = self._config.get("ghurub_offset", 15)
        forbidden_now = _is_in_forbidden_slot(shuruq, maghrib, dhuhr, tulu_offset, istiwa_offset, ghurub_offset)
        forbidden_slots = {
            "tulu_start": shuruq,
            "tulu_end": _add_minutes(shuruq, tulu_offset),
            "istiwa_start": _add_minutes(dhuhr, -istiwa_offset),
            "istiwa_end": dhuhr,
            "ghurub_start": _add_minutes(maghrib, -ghurub_offset),
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
        all_events = _find_events(today, 365)
        event_by_type = _build_event_index(all_events)
        next_event = all_events[0] if all_events else None

        # Tomorrow's prayer times (needed for next prayer calculation and tomorrow imsak)
        tomorrow_prayer_times = await self.hass.async_add_executor_job(
            _calculate_prayer_times, lat, lon, calc_method, adjustments,
            today + timedelta(days=1),
            fajr_angle, isha_angle
        )

        # Next prayer time
        next_prayer = _get_next_prayer(prayer_times, tomorrow_prayer_times)

        # Tomorrow's Imsak (Fajr of next day - 10 min)
        tomorrow_fajr = tomorrow_prayer_times.get("fajr", INVALID_TIME) if tomorrow_prayer_times else INVALID_TIME
        tomorrow_imsak = _add_minutes(tomorrow_fajr, -10)

        # Tomorrow's 5 mandatory prayers
        tomorrow_prayers = {
            "fajr": tomorrow_prayer_times.get("fajr", INVALID_TIME),
            "dhuhr": tomorrow_prayer_times.get("dhuhr", INVALID_TIME),
            "asr": tomorrow_prayer_times.get("asr", INVALID_TIME),
            "maghrib": tomorrow_prayer_times.get("maghrib", INVALID_TIME),
            "isha": tomorrow_prayer_times.get("isha", INVALID_TIME),
        }

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
            "next_prayer": next_prayer,
            "tomorrow_imsak": tomorrow_imsak,
            "tomorrow_prayers": tomorrow_prayers,
            "tomorrow_prayer_times": tomorrow_prayer_times,
        }


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
    if not time_str or time_str == INVALID_TIME:
        return 0
    try:
        parts = time_str.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return 0


def _calculate_tahajud(isha: str, fajr_tomorrow: str) -> str:
    try:
        isha_min = _time_to_minutes(isha)
        fajr_min = _time_to_minutes(fajr_tomorrow)
        if fajr_min <= isha_min:
            fajr_min += 24 * 60
        nuit = fajr_min - isha_min
        tahajud = isha_min + int(nuit * 2 / 3)
        hour = (tahajud // 60) % 24
        minute = tahajud % 60
        return f"{hour:02d}:{minute:02d}"
    except Exception:
        return INVALID_TIME


def _is_in_forbidden_slot(shuruq: str, maghrib: str, dhuhr: str, tulu_offset: int = 20, istiwa_offset: int = 10, ghurub_offset: int = 15) -> bool:
    now = datetime.now()
    now_min = now.hour * 60 + now.minute
    s1_start = _time_to_minutes(shuruq)
    s1_end = s1_start + tulu_offset
    s2_start = _time_to_minutes(dhuhr) - istiwa_offset
    s2_end = _time_to_minutes(dhuhr)
    s3_start = _time_to_minutes(maghrib) - ghurub_offset
    s3_end = _time_to_minutes(maghrib)
    if s3_start < 0:
        s3_start += 24 * 60
        s3_end += 24 * 60
    in_slot1 = s1_start <= now_min < s1_end
    in_slot2 = s2_start <= now_min < s2_end
    in_slot3 = s3_start <= now_min < s3_end
    return in_slot1 or in_slot2 or in_slot3


def _calculate_prayer_times(
    lat: float, lon: float, calc_method: str,
    adjustments: Dict[str, int], target_date,
    fajr_angle: float = None, isha_angle: float = None
) -> Dict[str, str]:
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        from adhanpy.PrayerTimes import PrayerTimes as AdhanPrayerTimes
        from adhanpy.calculation.CalculationMethod import CalculationMethod
        from adhanpy.calculation.CalculationParameters import CalculationParameters

        method_map = {
            "isna": CalculationMethod.NORTH_AMERICA,
            "mwl": CalculationMethod.MUSLIM_WORLD_LEAGUE,
            "makkah": CalculationMethod.UMM_AL_QURA,
            "egypt": CalculationMethod.EGYPTIAN,
            "karachi": CalculationMethod.KARACHI,
            "koc": CalculationMethod.KUWAIT,
            "kuwait": CalculationMethod.KUWAIT,
            "qatar": CalculationMethod.QATAR,
            "singapore": CalculationMethod.SINGAPORE,
            "france": CalculationMethod.UOIF,
            "turkey": CalculationMethod.NONE,
            "jafari": CalculationMethod.NONE,
            "london": CalculationMethod.NORTH_AMERICA,
            "dubai": CalculationMethod.DUBAI,
        }

        if calc_method == "custom" and fajr_angle is not None and isha_angle is not None:
            params = CalculationParameters(fajr_angle=fajr_angle, isha_angle=isha_angle)
            pt = AdhanPrayerTimes((lat, lon), datetime.combine(target_date, datetime.min.time()), calculation_parameters=params)
        else:
            method = method_map.get(calc_method, CalculationMethod.UMM_AL_QURA)
            pt = AdhanPrayerTimes((lat, lon), datetime.combine(target_date, datetime.min.time()), calculation_method=method)

        def dt_to_str(dt):
            if dt is None:
                return INVALID_TIME
            return dt.strftime("%H:%M")

        def apply_adj(time_str, adj):
            if time_str == INVALID_TIME:
                return INVALID_TIME
            return _add_minutes(time_str, adj)

        result = {
            "fajr": apply_adj(dt_to_str(pt.fajr), adjustments.get("Fajr", 0)),
            "shuruq": dt_to_str(pt.sunrise),
            "dhuhr": apply_adj(dt_to_str(pt.dhuhr), adjustments.get("Dhuhr", 0)),
            "asr": apply_adj(dt_to_str(pt.asr), adjustments.get("Asr", 0)),
            "maghrib": apply_adj(dt_to_str(pt.maghrib), adjustments.get("Maghrib", 0)),
            "isha": apply_adj(dt_to_str(pt.isha), adjustments.get("Isha", 0)),
        }
        return result
    except Exception as e:
        _LOGGER.error(f"Prayer times calculation failed: {e}")
        return {}


def _calculate_iqamah(prayer_times: Dict, offsets: Dict) -> Dict[str, str]:
    result = {}
    for prayer in ["fajr", "dhuhr", "asr", "maghrib", "isha"]:
        time = prayer_times.get(prayer, INVALID_TIME)
        offset = offsets.get(prayer.title(), 10)
        result[f"iqamah_{prayer}"] = _add_minutes(time, offset)
    return result


def _get_hijri_info(target_date) -> Dict:
    try:
        import hijridate
        h = hijridate.Gregorian(target_date.year, target_date.month, target_date.day).to_hijri()
        return {"day": h.day, "month": h.month, "year": h.year}
    except Exception:
        return {"day": 1, "month": 1, "year": 1447}


def _find_events(start_date, count: int = 365) -> list:
    events = []
    current = start_date
    prev_month = None
    found = 0
    for _ in range(400):
        if found >= count:
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
                found += 1
            # Last 10 Nights of Ramadan
            if h.month == 9 and 21 <= h.day <= 30:
                ev = {
                    "name": "Last 10 Nights of Ramadan",
                    "arabic": "العشر الأواخر من رمضان",
                    "date": current.isoformat(),
                    "gregorian": current.strftime("%Y-%m-%d"),
                    "hijri": f"{h.day:02d}-{h.month:02d}-{h.year}",
                }
                events.append(ev)
                found += 1
            # 10 Most Blessed Days
            if h.month == 12 and 1 <= h.day <= 10:
                ev = {
                    "name": "10 Most Blessed Days",
                    "arabic": "العشر ذي الحجة",
                    "date": current.isoformat(),
                    "gregorian": current.strftime("%Y-%m-%d"),
                    "hijri": f"{h.day:02d}-{h.month:02d}-{h.year}",
                }
                events.append(ev)
                found += 1
            prev_month = h.month
            current += timedelta(days=1)
        except Exception:
            current += timedelta(days=1)
    events.sort(key=lambda x: x.get("gregorian", ""))
    return events[:count]


def _build_event_index(events: list) -> dict:
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


def _get_next_prayer(prayer_times: Dict[str, str], tomorrow_prayer_times: Dict = None) -> Dict:
    now = datetime.now()
    now_min = now.hour * 60 + now.minute
    prayers_order = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
    prayer_keys = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
    next_prayer_name = None
    next_prayer_time = None
    next_prayer_key = None
    for i, key in enumerate(prayer_keys):
        time_str = prayer_times.get(key, INVALID_TIME)
        if time_str == INVALID_TIME:
            continue
        prayer_min = _time_to_minutes(time_str)
        if prayer_min > now_min:
            next_prayer_name = prayers_order[i]
            next_prayer_time = time_str
            next_prayer_key = key
            break
    if next_prayer_name is None:
        next_prayer_name = "Fajr"
        next_prayer_key = "fajr"
        next_prayer_time = tomorrow_prayer_times.get("fajr", INVALID_TIME) if tomorrow_prayer_times else INVALID_TIME
    if next_prayer_time != INVALID_TIME:
        next_min = _time_to_minutes(next_prayer_time)
        if next_min <= now_min:
            minutes_until = (24 * 60 - now_min) + next_min
        else:
            minutes_until = next_min - now_min
    else:
        minutes_until = 0
    return {
        "name": next_prayer_name,
        "key": next_prayer_key,
        "time": next_prayer_time,
        "minutes_until": minutes_until,
        "iqamah": _add_minutes(next_prayer_time, 10) if next_prayer_time != INVALID_TIME else INVALID_TIME,
    }
