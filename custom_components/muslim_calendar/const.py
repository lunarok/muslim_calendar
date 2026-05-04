"""
Muslim Calendar - Constantes partagees.
"""

DOMAIN = "muslim_calendar"
DEVICE_NAME = "Muslim Calendar"
DEVICE_MANUFACTURER = "Muslim Calendar"
DEVICE_MODEL = "Islamic Prayer Times"

DEFAULT_LOCATION = {"name": "Home (zone.home)", "lat": 47.4, "lon": -0.64}

CALC_METHODS = {
    "isna": "Islamic Society of North America (ISNA)",
    "mwl": "Muslim World League",
    "makkah": "Umm Al-Qura University, Makkah",
    "egypt": "Egyptian General Authority",
    "karachi": "University of Karachi",
    "koc": "Khalid Al Ghaml",
    "kuwait": "Kuwaiti Ministry of Awqaf",
    "qatar": "Qatar Calendar House",
    "singapore": "Islamic Religious Council of Singapore",
    "france": "France (WaqfSync / Ligo)",
    "turkey": "Presidency of Religious Affairs of Turkey",
    "jafari": "Shia Ithna Asheri",
    "london": "London Unified Mosque Board",
    "dubai": "Dubai International Awqaf",
    "custom": "Custom (fajr_angle, isha_angle)",
}

HIJRI_MONTHS_EN = {
    1: "Muharram", 2: "Safar", 3: "Rabi al-Awwal", 4: "Rabi al-Akhir",
    5: "Jumada al-Awwal", 6: "Jumada al-Akhir", 7: "Rajab", 8: "Sha'ban",
    9: "Ramadan", 10: "Shawwal", 11: "Dhu al-Qa'dah", 12: "Dhu al-Hijjah",
}

HIJRI_MONTH_KEYS = {
    1: "muharram", 2: "safar", 3: "rabi_al_awwal", 4: "rabi_al_akhir",
    5: "jumada_al_awwal", 6: "jumada_al_akhir", 7: "rajab", 8: "shaban",
    9: "ramadan", 10: "shawwal", 11: "dhu_al_qadah", 12: "dhu_al_hijjah",
}

ISLAMIC_EVENTS = {
    (1, 1): {"name": "Islamic New Year", "arabic": "رأس السنة الهجرية"},
    (1, 10): {"name": "Ashura", "arabic": "عاشوراء"},
    (3, 12): {"name": "Mawlid al-Nabi", "arabic": "مولد النبي ﷺ"},
    (7, 27): {"name": "Al-Isra wal-Miraj", "arabic": "الإسراء والمعراج"},
    (8, 15): {"name": "Laylat al-Barahah", "arabic": "ليلة البَرَاءة"},
    (9, 1): {"name": "First Day of Ramadan", "arabic": "أول رمضان"},
    (9, 21): {"name": "Last 10 Nights of Ramadan", "arabic": "العشر الأواخر من رمضان"},
    (9, 27): {"name": "Laylat al-Qadr", "arabic": "ليلة القدر"},
    (10, 1): {"name": "Eid al-Fitr", "arabic": "عيد الفطر"},
    (12, 1): {"name": "10 Most Blessed Days", "arabic": "العشر ذي الحجة"},
    (12, 9): {"name": "Day of Arafat", "arabic": "يوم عرفة"},
    (12, 10): {"name": "Eid al-Adha", "arabic": "عيد الأضحى"},
}
