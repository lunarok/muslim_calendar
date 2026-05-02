# Muslim Calendar

Plugin Home Assistant Community Store (HACS) pour les heures de priere islamiques et le calendrier Hijri.

## Fonctionnalites

- **15 methodes de calcul** des heures de priere (ISNA, Makkah, MWL, Karachi, France, etc.)
- **Ajustement numerique** de chaque priere obligatoire (+/- en minutes)
- **Iqamah parametrable** par priere (decalage en minutes)
- **Calendrier Hijri** : jour, mois, annee separes, mois suivants, evenements majeurs
- **1 Device** avec **~20 Entites** dans Home Assistant
- **Configuration via l'UI** Home Assistant (plus besoin de fichier YAML)

## Heures de priere publiees

| Entite | Description |
|---|---|
| `sensor.salat_fajr` | Fajr |
| `sensor.salat_lever_du_soleil` | Lever du soleil (Shuruuq) |
| `sensor.salat_dhuhr` | Dhuhr |
| `sensor.salat_asr` | Asr |
| `sensor.salat_maghrib` | Maghrib |
| `sensor.salat_isha` | Isha |
| `sensor.salat_minuit` | Minuit |
| `sensor.salat_imsak` | Imsak (10 min avant Fajr) |
| `sensor.salat_fin_fajr` | Fin du creneau Fajr (= Imsak) |
| `sensor.salat_debut_creneau_interdit` | Debut creneau interdit (Fajr) |
| `sensor.salat_fin_creneau_interdit` | Fin creneau interdit (Sunrise) |
| `sensor.salat_iqamah_*` | Heures Iqamah (Fajr, Dhuhr, Asr, Maghrib, Isha) |
| `sensor.salat_jour_hijri` | Jour Hijri (entier) |
| `sensor.salat_mois_hijri` | Mois Hijri (entier) |
| `sensor.salat_annee_hijri` | Annee Hijri (entier) |
| `sensor.salat_mois_hijri` | Mois Hijri avec attributes (prochain mois + 12 debuts) |
| `sensor.salat_evenements_islamiques` | Evenements avec attributes (prochain + 10 evenements) |

## Installation

### Methode 1 - Via HACS (recommande)

1. Ouvrez HACS dans Home Assistant
2. Cliquez sur **Add** → **Custom Repository**
3. Ajoutez : `https://github.com/lunarok/muslim_calendar`
4. Selectionnez **Integration**
5. Cliquez sur **Download**
6. Redemarrez Home Assistant

### Methode 2 - Manuel

```bash
cd /config/custom_components/
git clone https://github.com/lunarok/muslim_calendar.git
# ou copiez le dossier muslim_calendar dans /config/custom_components/
```

## Configuration

1. Allez dans **Settings → Devices & Services → Add Integration**
2. Recherchez **Muslim Calendar**
3. Remplissez les parametres :
   - **Latitude / Longitude** : coordonnees GPS du lieu
   - **Methode de calcul** : ISNA, Makkah, MWL, Karachi, France…
   - **Ajustements** : decalage en minutes pour chaque priere (optionnel)
   - **Iqamah** : decalage en minutes apres chaque priere (optionnel)

## Ajustements disponibles

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

## Methodes de calcul

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

## Attributes avances

### Capteur "Mois Hijri"
- `next_month_name` : nom du prochain mois
- `next_month_date` : date gregorienne du debut du prochain mois
- `next_month_hijri` : date Hijri du prochain mois
- `months` : liste des 12 prochains debuts de mois (name, date, hijri, month)

### Capteur "Evenements Islamiques"
- `next_event_name` : nom du prochain evenement
- `next_event_date` : date gregorienne
- `next_event_hijri` : date Hijri
- `next_event_arabic` : nom en arabe
- `events` : liste des 10 prochains evenements (name, date, hijri, arabic)

## Automatisations exemples

```yaml
automation:
  - alias: "Rappel Fajr"
    trigger:
      - platform: time
        at: "sensor.salat_fajr"
    action:
      - service: notify.mobile_app_telephone
        data:
          message: "Il est l'heure du Fajr"

  - alias: "Notification Ramadan"
    trigger:
      - platform: state
        entity_id: sensor.salat_evenements_islamiques
    condition:
      - condition: state
        entity_id: sensor.salat_evenements_islamiques
        attribute: next_event_name
        value: "Debut Ramadan"
    action:
      - service: notify.all
        data:
          message: "Le Ramadan commence aujourd'hui !"
```

## Developpement

```bash
# Structure du plugin
muslim_calendar/
├── manifest.json
├── __init__.py
├── config_flow.py
├── const.py
├── sensor.py
├── translations/
│   └── fr.json
└── README.md

# Tests locaux
cd /config/custom_components/muslim_calendar
pip install hijri-converter prayer-times-calculator
```

## Credits

- Bibliotheque `prayer-times-calculator` pour les heures de priere
- Bibliotheque `hijri-converter` pour les dates Hijri
- Inspiré du projet `muslim_prayer_companion` de @amaharek
