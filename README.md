# Muslim Calendar

Home Assistant Community Store (HACS) integration for Islamic prayer times and Hijri calendar. 100% local calculation — no external API calls.

## Features

- **15 calculation methods** for prayer times (ISNA, Makkah, MWL, Karachi, Qatar, Singapore, France, etc.)
- **Custom method** with configurable fajr/isha angles
- **Numeric adjustment** per prayer (+/- minutes)
- **Configurable Iqamah** per prayer (offset in minutes)
- **Automatic location** via Home Assistant zones and mobile apps
- **~25 entities** in Home Assistant
- **Native Calendar entity** — appears in HA Calendar view
- **Qibla direction** sensor (degrees + cardinal)
- **Tahajjud** automatic (last third of night)
- **Makruh Ibadah** (forbidden slots) with binary state
- **Configuration via UI** — no YAML needed

## Dependencies

| Library | Purpose |
|---|---|
| `adhanpy>=1.0.0` | Prayer times calculation (100% local) |
| `hijridate>=2.3.0` | Hijri/Gregorian date conversion |

## Installation

### Via HACS (recommended)

1. Open HACS → Add → Custom Repository
2. Add: `https://github.com/lunarok/muslim_calendar`
3. Select **Integration**
4. Click **Download**
5. Restart Home Assistant

## Entities Created

### Prayer Times (6 sensors)
`prayer_fajr`, `prayer_shuruq`, `prayer_dhuhr`, `prayer_asr`, `prayer_maghrib`, `prayer_isha`

### Iqamah (5 sensors)
`iqamah_fajr`, `iqamah_dhuhr`, `iqamah_asr`, `iqamah_maghrib`, `iqamah_isha`

### Special (2 sensors)
`special_imsak` (10 min before Fajr), `special_tahajjud` (2/3 between Isha and next Fajr)

### Next Prayer (2 sensors)
`next_prayer` (name), `next_prayer_time` (time string)

### Tomorrow (2 sensors)
`tomorrow_imsak`, `tomorrow_prayers` (all 5 prayers)

### Hijri Date (2 sensors)
`hijri_date`, `tomorrow_hijri_date` — each with 5 attributes: hijri_day, hijri_month, hijri_month_full, hijri_year, hijri_date_full

### Next Months (1 sensor)
12 attributes — one per Hijri month start date

### Events (1 sensor)
Next event + all 12 Islamic events indexed by name

### Makruh Ibadah (1 sensor)
Binary state (1/0) + 6 time slot attributes (tulu, istiwa, ghurub windows)

### Qibla Direction (1 sensor)
Degrees from North + cardinal direction (N, NE, SE, etc.)

### Native Calendar Entity
`calendar.muslim_calendar_calendar` — Islamic events and Hijri month starts

## Location Menu

Automatically detects:
- **`zone.home`** — home location from HA zones
- **Mobile app device trackers** — phones with the Companion app (identified by `source_type: mobile_app`)

## Calculation Methods

| Key | Description |
|---|---|
| `isna` | North America (ISNA) |
| `makkah` | Umm al-Qura, Makkah |
| `mwl` | Muslim World League |
| `karachi` | University of Karachi |
| `egypt` | Egyptian General Authority |
| `koc` | Kuwaiti Ministry (KOC) |
| `kuwait` | Kuwait |
| `qatar` | Qatar Calendar House |
| `singapore` | Islamic Religious Council of Singapore |
| `france` | UOIF (France) |
| `turkey` | Presidency of Religious Affairs of Turkey |
| `jafari` | Shia Ithna Asheri (Jafari) |
| `london` | London Unified Mosque Board |
| `dubai` | Dubai International Awqaf |
| `custom` | Custom — requires fajr_angle and isha_angle |

## Configuration Parameters

| Parameter | Description | Default |
|---|---|---|
| `adjust_fajr` | Offset for Fajr (+/- min) | 0 |
| `adjust_dhuhr` | Offset for Dhuhr | 0 |
| `adjust_asr` | Offset for Asr | 0 |
| `adjust_maghrib` | Offset for Maghrib | 0 |
| `adjust_isha` | Offset for Isha | 0 |
| `iqamah_fajr` | Iqamah delay after Fajr | 10 min |
| `iqamah_dhuhr` | Iqamah delay after Dhuhr | 10 min |
| `iqamah_asr` | Iqamah delay after Asr | 10 min |
| `iqamah_maghrib` | Iqamah delay after Maghrib | 5 min |
| `iqamah_isha` | Iqamah delay after Isha | 5 min |
| `fajr_angle` | Fajr angle (custom method) | 18.0 |
| `isha_angle` | Isha angle (custom method) | 18.0 |
| `tulu_offset` | Tulu (sunrise) slot duration | 20 min |
| `istiwa_offset` | Istiwa (zawwal) slot duration | 10 min |
| `ghurub_offset` | Ghurub (sunset) slot duration | 15 min |

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
      - service: notify.mobile_app_phone
        data:
          message: "You are in a makruh prayer time slot"

  - alias: "Next Prayer in 15 minutes"
    trigger:
      - platform: numeric_state
        entity_id: sensor.muslim_calendar_next_prayer
        attribute: minutes_until
        below: 15
    action:
      - service: notify.mobile_app_phone
        data:
          message: >-
            {{ state_attr('sensor.muslim_calendar_next_prayer', 'next_prayer_name') }}
            in {{ state_attr('sensor.muslim_calendar_next_prayer', 'minutes_until') }} minutes
```

## Plugin Structure

```
custom_components/muslim_calendar/
├── __init__.py        # Integration + coordinator
├── config_flow.py    # Configuration UI (ConfigFlow + OptionsFlow)
├── const.py          # Constants, methods, Hijri months, events
├── sensor.py         # All sensors (~25 entities)
├── calendar.py       # Native HA Calendar entity
├── manifest.json     # Version 2.0.7, requirements
├── translations/    # UI strings (fr, en, id, ms, de, tr, ar, zh, it, es, ur, fa)
└── brand/           # Icons for HACS (icon.png, logo.png, @2x variants)
```

## Supported Languages

UI translations available: French (fr), English (en), Indonesian (id), Malay (ms), German (de), Turkish (tr), Arabic (ar), Chinese (zh), Italian (it), Spanish (es), Urdu/Pakistani (ur), Persian/Farsi (fa)

## Credits

- [adhanpy](https://github.com/alphahm/adhanpy) — prayer times calculation (local, no API)
- [hijridate](https://github.com/hijridate/hijridate) — Hijri date conversion