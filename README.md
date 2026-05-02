# Muslim Calendar

Plugin Home Assistant Community Store (HACS) pour les heures de priere islamiques et le calendrier Hijri.

## Fonctionnalites

- **15 methodes de calcul** des heures de priere (ISNA, Makkah, MWL, Karachi, France, etc.)
- **Ajustement numerique** de chaque priere obligatoire (+/- en minutes)
- **Iqamah parametrable** par priere (decalage en minutes)
- **Localisation automatique** via les zones Home Assistant et les apps mobiles
- **Tahajud** automatique (dernier tiers de la nuit)
- **Creneaux interdits** avec etat binaire (0/1)
- **Calendrier iCal** pour l'entite Calendar HA
- **1 Device** avec **~16 Entites** dans Home Assistant

## Installation

### Via HACS (recommande)

1. HACS → Add → Custom Repository → `https://github.com/lunarok/muslim_calendar`
2. Selectionnez **Integration** → Download
3. Redemarrez Home Assistant

## Entites creees

### Heures de priere (7 capteurs)

| Entite | Description |
|---|---|
| `sensor.muslim_calendar_prayer_fajr` | Fajr |
| `sensor.muslim_calendar_prayer_shuruq` | Shuruq (Lever du soleil) |
| `sensor.muslim_calendar_prayer_dhuhr` | Dhuhr |
| `sensor.muslim_calendar_prayer_asr` | Asr |
| `sensor.muslim_calendar_prayer_maghrib` | Maghrib |
| `sensor.muslim_calendar_prayer_isha` | Isha |
| `sensor.muslim_calendar_prayer_midnight` | Minuit |

### Iqamah (5 capteurs)

| Entite | Description |
|---|---|
| `sensor.muslim_calendar_iqamah_fajr` | Iqamah Fajr |
| `sensor.muslim_calendar_iqamah_dhuhr` | Iqamah Dhuhr |
| `sensor.muslim_calendar_iqamah_asr` | Iqamah Asr |
| `sensor.muslim_calendar_iqamah_maghrib` | Iqamah Maghrib |
| `sensor.muslim_calendar_iqamah_isha` | Iqamah Isha |

### Capteurs speciaux (2 capteurs)

| Entite | Description |
|---|---|
| `sensor.muslim_calendar_special_imsak` | Imsak (10 min avant Fajr) |
| `sensor.muslim_calendar_special_tahajud` | Tahajud (2/3 entre Isha et Fajr lendemain) |

### Capteur Date Hijri (1 capteur, 5 attributs)

**State** : date complete (ex: `10 Ramadan 1447`)

| Attribut | Type | Description |
|---|---|---|
| `hijri_day` | int | Jour Hijri |
| `hijri_month` | int | Mois Hijri |
| `hijri_month_full` | str | Nom complet du mois |
| `hijri_year` | int | Annee Hijri |
| `hijri_date_full` | str | Date complete formatee |

### Capteur Mois Prochain (1 capteur, attributs)

**State** : date gregorienne du debut du prochain mois Hijri (ex: `2026-02-18`)

| Attribut | Description |
|---|---|
| `next_month_name` | Nom du prochain mois |
| `next_month_hijri` | Date Hijri du debut |
| `months` | Liste des 12 prochains debuts de mois |

### Capteur Evenements Islamiques (1 capteur, 16 attributs)

**State** : nom du prochain evenement

| Attribut | Description |
|---|---|
| `next_event_name` | Nom du prochain evenement |
| `next_event_date` | Date gregorienne |
| `next_event_hijri` | Date Hijri |
| `next_event_arabic` | Nom en arabe |
| `event_nouvel_an_hijri` | Prochaine date de ce type |
| `event_achoura` | Prochaine date de ce type |
| `event_mawlid_al_nabi` | Prochaine date de ce type |
| `event_al_isra_wal_miraj` | Prochaine date de ce type |
| `event_laylat_al_barahah` | Prochaine date de ce type |
| `event_debut_ramadan` | Prochaine date de ce type |
| `event_laylat_al_qadr` | Prochaine date de ce type |
| `event_aid_al_fitr` | Prochaine date de ce type |
| `event_jour_de_arafat` | Prochaine date de ce type |
| `event_aid_al_adha` | Prochaine date de ce type |
| `events` | Liste des 10 prochains evenements |

### Capteur Creneaux Interdits (1 capteur, 7 attributs)

**State** : `1` si dans un slot interdit, `0` sinon

Les 3 slots representent les moments ou la priere est makruh :

| Attribut | Description |
|---|---|
| `slot1_start` | Shuruq |
| `slot1_end` | Shuruq + 20 min |
| `slot2_start` | Dhuhr (zawwal) |
| `slot2_end` | Dhuhr + 20 min |
| `slot3_start` | Maghrib - 20 min |
| `slot3_end` | Maghrib |

### Capteur Calendrier Islamique (1 capteur, 1 attribut)

Pour l'entite Calendar Home Assistant.

| Attribut | Description |
|---|---|
| `events` | Contenu iCal complet (VCALENDAR) |

Pour ajouter le calendrier dans HA, ajoutez une entite Calendar via l'UI avec :
- Entity ID : `calendar.muslim_calendar_calendar`
- URL source : `calendar.muslim_calendar_calendar`

Ou utilisez le contenu iCal dans `events` avec l'integration Calendar Generic.

## Menu de localisation

Le plugin detecte automatiquement :

- **`zone.home`** — votre maison
- **Devices trackers des apps mobiles** — telephones avec l'app Companion

## Automatisations exemples

```yaml
automation:
  - alias: "Notification Debut Ramadan"
    trigger:
      - platform: state
        entity_id: sensor.muslim_calendar_hijri_events
    condition:
      - condition: state
        entity_id: sensor.muslim_calendar_hijri_events
        attribute: next_event_name
        value: "Debut Ramadan"
    action:
      - service: notify.all
        data:
          message: "Le Ramadan commence aujourd'hui !"

  - alias: "Creneau interdit - ne pas prier"
    trigger:
      - platform: state
        entity_id: sensor.muslim_calendar_forbidden_slots
    condition:
      - condition: state
        entity_id: sensor.muslim_calendar_forbidden_slots
        state: "1"
    action:
      - service: notify.mobile_app
        data:
          message: "Vous etes dans un creneau ou la priere est declassee makruh"

  - alias: "Tahajud - dernier tiers de la nuit"
    trigger:
      - platform: time
        at: "sensor.muslim_calendar_special_tahajud"
    action:
      - service: notify.mobile_app
        data:
          message: "L'heure du Tahajud a sonne. C'est le derniers tiers de la nuit."
```

## Credits

- `prayer-times-calculator` — heures de priere
- `hijri-converter` — dates Hijri
