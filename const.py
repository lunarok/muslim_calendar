"""
Muslim Calendar - Constantes partagees.
"""

DOMAIN = "muslim_calendar"
DEVICE_NAME = "Salat"
DEVICE_MANUFACTURER = "Muslim Calendar"
DEVICE_MODEL = "Islamic Prayer Times"

CALC_METHODS = {
    "isna": "Islamic Society of North America",
    "mwl": "Muslim World League",
    "karachi": "University of Islamic Sciences, Karachi",
    "makkah": "Umm al-Qura University, Makkah",
    "egypt": "Egyptian General Authority of Survey",
    "tehran": "Institute of Geophysics, University of Tehran",
    "jafari": "Jafari",
    "france": "France (UOIF)",
}

HIJRI_MONTHS_FR = {
    1: "Muharram", 2: "Safar", 3: "Rabi al-Awwal", 4: "Rabi al-Akhir",
    5: "Jumada al-Awwal", 6: "Jumada al-Akhir", 7: "Rajab", 8: "Sha'ban",
    9: "Ramadan", 10: "Shawwal", 11: "Dhu al-Qa'dah", 12: "Dhu al-Hijjah",
}

ISLAMIC_EVENTS = {
    (1, 1): {"name": "Nouvel An Hijri", "arabic": "رأس السنة الهجرية"},
    (1, 10): {"name": "Achoura", "arabic": "عاشوراء"},
    (3, 12): {"name": "Mawlid al-Nabi", "arabic": "مولد النبي ﷺ"},
    (7, 27): {"name": "Al-Isra wal-Miraj", "arabic": "الإسراء والمعراج"},
    (8, 15): {"name": "Laylat al-Barahah", "arabic": "ليلة البَرَاءة"},
    (9, 1): {"name": "Debut Ramadan", "arabic": "أول رمضان"},
    (9, 27): {"name": "Laylat al-Qadr", "arabic": "ليلة القدر"},
    (10, 1): {"name": "Aid al-Fitr", "arabic": "عيد الفطر"},
    (12, 9): {"name": "Jour de Arafat", "arabic": "يوم عرفة"},
    (12, 10): {"name": "Aid al-Adha", "arabic": "عيد الأضحى"},
}
