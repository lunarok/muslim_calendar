# Muslim Calendar

Home Assistant Community Store (HACS) integration for Islamic prayer times and Hijri calendar.

## Features

- **15 calculation methods** for prayer times (ISNA, Makkah, MWL, Karachi, France, etc.)
- **Numeric adjustment** for each mandatory prayer (+/- in minutes)
- **Configurable Iqamah** per prayer (offset in minutes)
- **Automatic location** via Home Assistant zones and mobile apps
- **1 Device** with **~14 Entities** in Home Assistant
- **Native Calendar entity** — appears directly in Home Assistant Calendar
- **Tahajjud** automatic (last third of night)
- **Makruh Ibadah** (forbidden prayer slots) with binary state
- **Configuration via UI** — no YAML needed

## Installation

### Via HACS (recommended)

1. Open HACS → Add → Custom Repository
2. Add: `https://github.com/lunarok/muslim_calendar`
3. Select **Integration**
4. Click **Download**
5. Restart Home Assistant

## Entities Created

### Prayer Times (6 sensors)

| Entity | Description |
|---|---|
| `sensor.muslim_calendar_prayer_fajr` | Fajr |
| `sensor.muslim_calendar_prayer_shuruq` | Shuruq (Sunrise) |
| `sensor.muslim_calendar_prayer_dhuhr` | Dhuhr |
| `sensor.muslim_calendar_prayer_asr` | Asr |
| `sensor.muslim_calendar_prayer_maghrib` | Maghrib |
| `sensor.muslim_calendar_prayer_isha` | Isha |

### Iqamah (5 sensors)

| Entity | Description |
|---|---|
| `sensor.muslim_calendar_iqamah_fajr` | Iqamah Fajr |
| `sensor.muslim_calendar_iqamah_dhuhr` | Iqamah Dhuhr |
| `sensor.muslim_calendar_iqamah_asr` | Iqamah Asr |
| `sensor.muslim_calendar_iqamah_maghrib` | Iqamah Maghrib |
| `sensor.muslim_calendar_iqamah_isha` | Iqamah Isha |

### Special Sensors (2 sensors)

| Entity | Description |
|---|---|
| `sensor.muslim_calendar_special_imsak` | Imsak (10 min before Fajr) |
| `sensor.muslim_calendar_special_tahajjud` | Tahajjud (2/3 between Isha and next Fajr) |

### Hijri Date Sensor (1 sensor, 5 attributes)

**State**: full date (ex: `10 Ramadan 1447`)

| Attribute | Type | Description |
|---|---|---|
| `hijri_day` | int | Hijri day |
| `hijri_month` | int | Hijri month |
| `hijri_month_full` | str | Full month name |
| `hijri_year` | int | Hijri year |
| `hijri_date_full` | str | Full formatted date |

### Next Months Sensor (1 sensor, attributes)

**State**: next Hijri month name (ex: `Ramadan`)

| Attribute | Description |
|---|---|
| `next_month_name` | Name of next Hijri month |
| `month_muharram` | Gregorian date of Muharram start |
| `month_safar` | Gregorian date of Safar start |
| ... | ... (all 12 months) |

### Events Sensor (1 sensor, 16 attributes)

**State**: next event name

| Attribute | Description |
|---|---|
| `next_event_name` | Next event name |
| `next_event_date` | Gregorian date |
| `next_event_hijri` | Hijri date |
| `next_event_arabic` | Name in Arabic |
| `event_islamic_new_year` | Next occurrence of this event |
| `event_ashura` | Next occurrence |
| `event_mawlid_al_nabi` | Next occurrence |
| ... | ... (10 event types) |

### Makruh Ibadah Sensor (1 sensor, 7 attributes)

**State**: `1` if currently in a forbidden slot, `0` otherwise

The 3 slots represent times when prayer is makruh:

| Attribute | Description |
|---|---|
| `tulu_start` | Shuruq (sunrise) |
| `tulu_end` | Shuruq + 20 min |
| istiwa_start | Dhuhr (zawwal) |
| istiwa_end | Dhuhr + 20 min |
| `ghurub_start` | Maghrib - 20 min |
| `ghurub_end` | Maghrib |

### Native Calendar Entity

A **Calendar** entity named `calendar.muslim_calendar_calendar` is automatically created and appears in Home Assistant's Calendar view. It contains all Islamic events and Hijri month starts.

## Location Menu

The plugin automatically detects:

- **`zone.home`** — your home location
- **Mobile app device trackers** — phones with the Companion app

## Adjustment Parameters

| Parameter | Description |
|---|---|
| `adjust_fajr` | Offset for Fajr (+/- in minutes) |
| `adjust_dhuhr` | Offset for Dhuhr |
| `adjust_asr` | Offset for Asr |
| `adjust_maghrib` | Offset for Maghrib |
| `adjust_isha` | Offset for Isha |
| `iqamah_fajr` | Iqamah delay after Fajr (default: 20 min) |
| `iqamah_dhuhr` | Iqamah delay after Dhuhr (default: 15 min) |
| `iqamah_asr` | Iqamah delay after Asr (default: 15 min) |
| `iqamah_maghrib` | Iqamah delay after Maghrib (default: 10 min) |
| `iqamah_isha` | Iqamah delay after Isha (default: 15 min) |

## Calculation Methods

| Method | Description |
|---|---|
| `isna` | Islamic Society of North America (default) |
| `makkah` | Umm al-Qura University, Makkah |
| `mwl` | Muslim World League |
| `karachi` | University of Islamic Sciences, Karachi |
| `egypt` | Egyptian General Authority of Survey |
| `tehran` | Institute of Geophysics, University of Tehran |
| `jafari` | Jafari |
| `france` | France (UOIF) |

## Automation Examples

```yaml
automation:
  - alias: "First Day of Ramadan Notification"
    trigger:
      - platform: state
        entity_id: sensor.muslim_calendar_events
    condition:
      - condition: state
        entity_id: sensor.muslim_calendar_events
        attribute: next_event_name
        value: "First Day of Ramadan"
    action:
      - service: notify.all
        data:
          message: "Ramadan starts today!"

  - alias: "Makruh Time Warning"
    trigger:
      - platform: state
        entity_id: sensor.muslim_calendar_makruh_ibadah
    condition:
      - condition: state
        entity_id: sensor.muslim_calendar_makruh_ibadah
        state: "1"
    action:
      - service: notify.mobile_app
        data:
          message: "You are in a makruh prayer time slot"

  - alias: "Tahajjud Reminder"
    trigger:
      - platform: time
        at: "sensor.muslim_calendar_special_tahajjud"
    action:
      - service: notify.mobile_app
        data:
          message: "Tahajjud time. This is the last third of the night."
```

## Development

```bash
# Plugin structure
muslim_calendar/
├── __init__.py       # Integration + coordinator
├── config_flow.py     # Configuration UI
├── const.py          # Constants
├── sensor.py         # Sensors
├── calendar.py       # Native Calendar entity
├── translations/
│   └── fr.json
├── brand/
│   └── icon.png
└── manifest.json

# Local testing
cd /config/custom_components/muslim_calendar
pip install hijridate prayer-times-calculator
```

## Credits

- `prayer-times-calculator` — prayer times
- `hijridate` — Hijri dates
