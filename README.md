# Muslim Calendar

Plugin Home Assistant Community Store (HACS) pour les heures de priere islamiques et le calendrier Hijri.

## Fonctionnalites

- **15 methodes de calcul** des heures de priere (ISNA, Makkah, MWL, Karachi, France, etc.)
- **Ajustement numerique** de chaque priere obligatoire (+/- en minutes)
- **Iqamah parametrable** par priere (decalage en minutes)
- **Localisation automatique** via les zones Home Assistant et les apps mobiles
- **1 Device** avec **~15 Entites** dans Home Assistant
- **Configuration via l'UI** Home Assistant (plus besoin de fichier YAML)

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
| `sensor.muslim_calendar_forbidden_slots` | Creneaux interdits a la priere |

### Capteur Date Hijri (1 capteur, 5 attributs)

**State** : date complete (ex: `10 Ramadan 1447`)

| Attribut | Description |
|---|---|
| `hijri_day` | Jour Hijri (entier) |
| `hijri_month` | Mois Hijri (entier) |
| `hijri_month_full` | Nom complet du mois |
| `hijri_year` | Annee Hijri (entier) |
| `hijri_date_full` | Date complete |

### Capteur Mois Hijri (1 capteur, attributs)

**State** : prochain mois Hijri

| Attribut | Description |
|---|---|
| `next_month_name` | Nom du prochain mois |
| `next_month_date` | Date gregorienne du debut |
| `next_month_hijri` | Date Hijri du debut |
| `months` | Liste des 12 prochains debuts de mois |

### Capteur Evenements Islamiques (1 capteur, attributs)

**State** : prochain evenement

| Attribut | Description |
|---|---|
| `next_event_name` | Nom du prochain evenement |
| `next_event_date` | Date gregorienne |
| `next_event_hijri` | Date Hijri |
| `next_event_arabic` | Nom en arabe |
| `events` | Liste des 10 prochains evenements |

### Capteur Creneaux Interdits (1 capteur, 6 attributs)

**State** : `slot1_start` (debut du slot 1)

Les 3 slots representent les moments ou la priere n'est pas recommandee :

| Attribut | Description |
|---|---|
| `slot1_start` | Shuruq (lever du soleil) |
| `slot1_end` | Shuruq + 20 minutes |
| `slot2_start` | Dhuhr (zawwal) |
| `slot2_end` | Dhuhr + 20 minutes |
| `slot3_start` | Maghrib - 20 minutes |
| `slot3_end` | Maghrib |

## Installation

### Via HACS (recommande)

1. Ouvrez HACS dans Home Assistant
2. Cliquez sur **Add** → **Custom Repository**
3. Ajoutez : `https://github.com/lunarok/muslim_calendar`
4. Selectionnez **Integration**
5. Cliquez sur **Download**
6. Redemarrez Home Assistant

### Manuel

```bash
cd /config/custom_components/
git clone https://github.com/lunarok/muslim_calendar.git
# ou copiez le dossier muslim_calendar dans /config/custom_components/
```

## Configuration

### Menu de localisation

Le plugin detecte automatiquement :

- **`zone.home`** — votre maison (coordonnees de la zone Home Assistant)
- **Devices trackers des apps mobiles** — chaque telephone avec l'app Companion installee

Lors de la configuration, selectionnez simplement la localisation desiree dans le menu. Si vous choisissez `Personnalisee`, vous pouvez entrer vos propres coordonnees GPS.

### Ajustements disponibles

| Parametre | Description |
|---|---|
| `adjust_fajr` | Decalage pour Fajr (+/- en minutes) |
| `adjust_dhuhr` | Decalage pour Dhuhr |
| `adjust_asr` | Decalage pour Asr |
| `adjust_maghrib` | Decalage pour Maghrib |
| `adjust_isha` | Decalage pour Isha |
| `iqamah_fajr` | Delai Iqamah apres Fajr (default: 20 min) |
| `iqamah_dhuhr` | Delai Iqamah apres Dhuhr (default: 15 min) |
| `iqamah_asr` | Delai Iqamah apres Asr (default: 15 min) |
| `iqamah_maghrib` | Delai Iqamah apres Maghrib (default: 10 min) |
| `iqamah_isha` | Delai Iqamah apres Isha (default: 15 min) |

### Methodes de calcul

| Methode | Description |
|---|---|
| `isna` | Islamic Society of North America (default) |
| `makkah` | Umm al-Qura University, Makkah |
| `mwl` | Muslim World League |
| `karachi` | University of Islamic Sciences, Karachi |
| `egypt` | Egyptian General Authority of Survey |
| `tehran` | Institute of Geophysics, University of Tehran |
| `jafari` | Jafari |
| `france` | France (UOIF) |

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

  - alias: "Rappel Imsak avant Fajr"
    trigger:
      - platform: time
        at: "sensor.muslim_calendar_special_imsak"
    action:
      - service: notify.mobile_app_telephone
        data:
          message: "L'Imsak est dans 10 minutes"

  - alias: "Eviter priere en creneau interdit"
    trigger:
      - platform: time
        at: "sensor.muslim_calendar_forbidden_slots"
    condition:
      - condition: state
        entity_id: input_boolean.ma_priere_en_cours
        state: "on"
    action:
      - service: timer.start
        data:
          entity_id: timer.delai_priere
          duration: "00:30:00"
```

## Developpement

```bash
# Structure du plugin
muslim_calendar/
├── manifest.json
├── __init__.py           # Integration + coordinator
├── config_flow.py         # Configuration UI
├── const.py               # Constantes
├── sensor.py              # Capteurs
├── translations/
│   └── fr.json
├── icon.jpg
└── README.md

# Tests locaux
cd /config/custom_components/muslim_calendar
pip install hijri-converter prayer-times-calculator
```

## Credits

- Bibliotheque `prayer-times-calculator` pour les heures de priere
- Bibliotheque `hijri-converter` pour les dates Hijri
