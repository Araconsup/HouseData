"""
Tehran geographic, district, and neighborhood definitions.
Includes all 22 official municipal districts and notable Divar neighborhoods
with accurate latitude/longitude ranges.
"""

from typing import Dict, List, Optional, Tuple

TEHRAN_DISTRICTS: Dict[int, Dict] = {
    1: {
        "name_fa": "منطقه ۱ (شمرانات)",
        "name_en": "District 1 (Shemiran)",
        "center": (35.8120, 51.4350),
        "lat_range": (35.7900, 35.8450),
        "lon_range": (51.3800, 51.5200),
        "neighborhoods": [
            "تجریش", "زعفرانیه", "الهیه", "نیاوران", "ولنجک", "فرمانیه",
            "قیطریه", "کامرانیه", "محمودیه", "دربند", "درکه", "جماران",
            "سوهانک", "دارآباد", "کاشانک", "آجودانیه", "چیذر", "اقدسیه",
        ],
    },
    2: {
        "name_fa": "منطقه ۲",
        "name_en": "District 2",
        "center": (35.7700, 51.3600),
        "lat_range": (35.7100, 35.8100),
        "lon_range": (51.3200, 51.3900),
        "neighborhoods": [
            "سعادت‌آباد", "شهرک غرب", "گیشا", "ستارخان", "صادقیه (شمالی)",
            "مرزداران", "شهرآرا", "تهران‌ویلا", "طرشت", "توحید", "پونک (جنوبی)", "علامه",
        ],
    },
    3: {
        "name_fa": "منطقه ۳",
        "name_en": "District 3",
        "center": (35.7650, 51.4300),
        "lat_range": (35.7400, 35.7900),
        "lon_range": (51.3900, 51.4700),
        "neighborhoods": [
            "ونک", "میرداماد", "ظفر", "جردن (آفریقا)", "قلهک", "دروس",
            "پاسداران", "اختیاریه", "احتشامیه", "کاووسیه", "داوودیه",
        ],
    },
    4: {
        "name_fa": "منطقه ۴",
        "name_en": "District 4",
        "center": (35.7500, 51.5100),
        "lat_range": (35.7100, 35.7900),
        "lon_range": (51.4600, 51.5800),
        "neighborhoods": [
            "تهرانپارس (غربی)", "تهرانپارس (شرقی)", "نارمک (شمالی)", "هروی",
            "حسین‌آباد", "پاسداران (شرقی)", "لویزان", "شمس‌آباد", "قاسم‌آباد", "کوهسار",
        ],
    },
    5: {
        "name_fa": "منطقه ۵",
        "name_en": "District 5",
        "center": (35.7500, 51.3100),
        "lat_range": (35.7100, 35.7900),
        "lon_range": (51.2700, 51.3500),
        "neighborhoods": [
            "صادقیه", "پونک", "شهران", "جنت‌آباد (مرکزی)", "جنت‌آباد (شمالی)",
            "جنت‌آباد (جنوبی)", "اکباتان", "فردوس (شرقی)", "فردوس (غربی)",
            "سازمان برنامه", "باغ فیض", "کوهسار", "آپادانا",
        ],
    },
    6: {
        "name_fa": "منطقه ۶",
        "name_en": "District 6",
        "center": (35.7200, 51.4100),
        "lat_range": (35.6950, 35.7450),
        "lon_range": (51.3800, 51.4400),
        "neighborhoods": [
            "یوسف‌آباد", "امیرآباد (کارگر شمالی)", "فاطمی", "کشاورز",
            "میدان ولیعصر", "کریم‌خان", "سنایی", "جمالزاده", "گاندی", "توانیر",
        ],
    },
    7: {
        "name_fa": "منطقه ۷",
        "name_en": "District 7",
        "center": (35.7200, 51.4450),
        "lat_range": (35.7000, 35.7450),
        "lon_range": (51.4250, 51.4700),
        "neighborhoods": [
            "سیدخندان", "سهروردی (شمالی)", "سهروردی (جنوبی)", "عباس‌آباد",
            "مطهری", "بهار", "امجدیه", "نظام‌آباد", "خواجه نظام",
        ],
    },
    8: {
        "name_fa": "منطقه ۸",
        "name_en": "District 8",
        "center": (35.7200, 51.4950),
        "lat_range": (35.6950, 35.7400),
        "lon_range": (51.4700, 51.5300),
        "neighborhoods": [
            "نارمک", "تهران‌نو", "مجیدیه (جنوبی)", "سبلان", "وحیدیه", "تسلیحات",
        ],
    },
    9: {
        "name_fa": "منطقه ۹",
        "name_en": "District 9",
        "center": (35.6900, 51.3400),
        "lat_range": (35.6700, 35.7100),
        "lon_range": (51.3100, 51.3750),
        "neighborhoods": [
            "میدان آزادی", "استاد معین", "دکتر هوشیار", "دستغیب", "مهرآباد جنوبی",
        ],
    },
    10: {
        "name_fa": "منطقه ۱۰",
        "name_en": "District 10",
        "center": (35.6850, 51.3750),
        "lat_range": (35.6700, 35.7000),
        "lon_range": (51.3550, 51.3950),
        "neighborhoods": [
            "بریانک", "سلسبیل", "کارون", "جیحون", "هفت‌چنار", "دامپزشکی", "قصرالدشت",
        ],
    },
    11: {
        "name_fa": "منطقه ۱۱",
        "name_en": "District 11",
        "center": (35.6850, 51.4000),
        "lat_range": (35.6650, 35.7000),
        "lon_range": (51.3850, 51.4200),
        "neighborhoods": [
            "منیریه", "حسن‌آباد", "شیخ هادی", "انقلاب", "امیریه", "فروزش",
        ],
    },
    12: {
        "name_fa": "منطقه ۱۲",
        "name_en": "District 12",
        "center": (35.6800, 51.4300),
        "lat_range": (35.6600, 35.7000),
        "lon_range": (51.4100, 51.4550),
        "neighborhoods": [
            "بهارستان", "پامنار", "بازار بزرگ تهران", "فردوسی", "دروازه شمیران", "سنگلج",
        ],
    },
    13: {
        "name_fa": "منطقه ۱۳",
        "name_en": "District 13",
        "center": (35.7000, 51.4900),
        "lat_range": (35.6800, 35.7200),
        "lon_range": (51.4600, 51.5400),
        "neighborhoods": [
            "پیروزی", "نیروی هوایی", "حافظیه", "دهقان", "آشتیانی",
        ],
    },
    14: {
        "name_fa": "منطقه ۱۴",
        "name_en": "District 14",
        "center": (35.6750, 51.4750),
        "lat_range": (35.6550, 35.6950),
        "lon_range": (51.4500, 51.5200),
        "neighborhoods": [
            "صددستگاه", "چهارصددستگاه", "پرستار", "شکوفه", "نبرد", "ابوذر",
        ],
    },
    15: {
        "name_fa": "منطقه ۱۵",
        "name_en": "District 15",
        "center": (35.6400, 51.4700),
        "lat_range": (35.6000, 35.6700),
        "lon_range": (51.4300, 51.5400),
        "neighborhoods": [
            "افسریه", "مشیریه", "کیانشهر", "مسعودیه", "بروجردی", "هاشم‌آباد",
        ],
    },
    16: {
        "name_fa": "منطقه ۱۶",
        "name_en": "District 16",
        "center": (35.6450, 51.4050),
        "lat_range": (35.6200, 35.6700),
        "lon_range": (51.3800, 51.4300),
        "neighborhoods": [
            "نازی‌آباد", "یاخچی‌آباد", "جوادیه", "خزانه بخارایی", "علی‌آباد",
        ],
    },
    17: {
        "name_fa": "منطقه ۱۷",
        "name_en": "District 17",
        "center": (35.6550, 51.3700),
        "lat_range": (35.6400, 35.6750),
        "lon_range": (51.3500, 51.3900),
        "neighborhoods": [
            "فلاح (ابوذر غربی)", "یافت‌آباد شرقی", "آذری", "امامزاده حسن",
        ],
    },
    18: {
        "name_fa": "منطقه ۱۸",
        "name_en": "District 18",
        "center": (35.6400, 51.3200),
        "lat_range": (35.6000, 35.6700),
        "lon_range": (51.2700, 51.3600),
        "neighborhoods": [
            "شادآباد", "شهرک ولیعصر", "یافت‌آباد", "تولیددارو",
        ],
    },
    19: {
        "name_fa": "منطقه ۱۹",
        "name_en": "District 19",
        "center": (35.6150, 51.3850),
        "lat_range": (35.5800, 35.6500),
        "lon_range": (51.3500, 51.4200),
        "neighborhoods": [
            "خانی‌آباد نو", "عبدالله‌آباد", "نعمت‌آباد", "اسفندیاری",
        ],
    },
    20: {
        "name_fa": "منطقه ۲۰ (شهر ری)",
        "name_en": "District 20 (Shahr-e-Rey)",
        "center": (35.5900, 51.4350),
        "lat_range": (35.5500, 35.6200),
        "lon_range": (51.3800, 51.4800),
        "neighborhoods": [
            "شهر ری", "دولت‌آباد", "صفاییه", "چشمه علی", "جوانمرد قصاب",
        ],
    },
    21: {
        "name_fa": "منطقه ۲۱",
        "name_en": "District 21",
        "center": (35.7000, 51.2400),
        "lat_range": (35.6700, 35.7300),
        "lon_range": (51.1800, 51.2800),
        "neighborhoods": [
            "تهرانسر", "شهرک آزادی", "باشگاه نفت", "شهرک ۲۲ بهمن", "وردآورد",
        ],
    },
    22: {
        "name_fa": "منطقه ۲۲ (چیتگر)",
        "name_en": "District 22 (Chitgar)",
        "center": (35.7400, 51.2100),
        "lat_range": (35.7000, 35.7800),
        "lon_range": (51.1400, 51.2700),
        "neighborhoods": [
            "دریاچه شهدای خلیج فارس (چیتگر)", "شهرک گلستان (راه‌آهن)",
            "دهکده المپیک", "زیبادشت", "کوهک", "شهرک شهید باقری",
        ],
    },
}

# Divar neighborhood slug to municipal district and Persian name mapping
DIVAR_SLUG_TO_DISTRICT: Dict[str, Tuple[int, str]] = {
    # District 1
    "tajrish": (1, "تجریش"),
    "zafaraniyeh": (1, "زعفرانیه"),
    "elahiyeh": (1, "الهیه"),
    "niavaran": (1, "نیاوران"),
    "velenjak": (1, "ولنجک"),
    "farmaniyeh": (1, "فرمانیه"),
    "gheytariyeh": (1, "قیطریه"),
    "kamraniyeh": (1, "کامرانیه"),
    "mahmoodiyeh": (1, "محمودیه"),
    "sohanak": (1, "سوهانک"),
    "darabad": (1, "دارآباد"),
    "aghdasieh": (1, "اقدسیه"),
    "ajodaniyeh": (1, "آجودانیه"),
    "chizar": (1, "چیذر"),

    # District 2
    "saadat-abad": (2, "سعادت‌آباد"),
    "allameh": (2, "علامه"),
    "shahrak-e-gharb": (2, "شهرک غرب"),
    "gisha": (2, "گیشا"),
    "sattarkhan": (2, "ستارخان"),
    "marzdaran": (2, "مرزداران"),
    "shahr-e-ara": (2, "شهرآرا"),
    "tarasht": (2, "طرشت"),
    "tehran-vila": (2, "تهران‌ویلا"),
    "tohid": (2, "توحید"),

    # District 3
    "vanak": (3, "ونک"),
    "mirdamad": (3, "میرداماد"),
    "zafar": (3, "ظفر"),
    "jordan": (3, "جردن"),
    "gholhak": (3, "قلهک"),
    "darous": (3, "دروس"),
    "pasdaran": (3, "پاسداران"),
    "ekhtiyariyeh": (3, "اختیاریه"),
    "davoodiyeh": (3, "داوودیه"),

    # District 4
    "tehranpars-western": (4, "تهرانپارس غربی"),
    "tehranpars-eastern": (4, "تهرانپارس شرقی"),
    "tehranpars": (4, "تهرانپارس"),
    "heravi": (4, "هروی"),
    "hossein-abad": (4, "حسین‌آباد"),
    "lavizan": (4, "لویزان"),
    "shams-abad": (4, "شمس‌آباد"),

    # District 5
    "sadeghiyeh": (5, "صادقیه"),
    "poonak": (5, "پونک"),
    "shahran": (5, "شهران"),
    "central-janat-abad": (5, "جنت‌آباد مرکزی"),
    "northern-janat-abad": (5, "جنت‌آباد شمالی"),
    "southern-janat-abad": (5, "جنت‌آباد جنوبی"),
    "ekbatan": (5, "اکباتان"),
    "eastern-ferdows": (5, "فردوس شرق"),
    "western-ferdows": (5, "فردوس غرب"),
    "bagh-e-feyz": (5, "باغ فیض"),
    "kousar": (5, "کوهسار"),

    # District 6
    "yousef-abad": (6, "یوسف‌آباد"),
    "north-karegar": (6, "کارگر شمالی"),
    "amirabad": (6, "امیرآباد"),
    "fatemi": (6, "فاطمی"),
    "keshavarz-blvd": (6, "بلوار کشاورز"),
    "valiasr-sq": (6, "میدان ولیعصر"),
    "karimkhan": (6, "کریم‌خان"),
    "gandi": (6, "گاندی"),
    "tavanir": (6, "توانیر"),

    # District 7
    "seyed-khandan": (7, "سیدخندان"),
    "sohrevardi": (7, "سهروردی"),
    "abbas-abad": (7, "عباس‌آباد"),
    "motahari": (7, "مطهری"),
    "nezam-abad": (7, "نظام‌آباد"),

    # District 8
    "narmak": (8, "نارمک"),
    "tehran-now": (8, "تهران‌نو"),
    "sabalan": (8, "سبلان"),
    "vahidieh": (8, "وحیدیه"),

    # District 9
    "azadi": (9, "آزادی"),
    "ostad-moein": (9, "استاد معین"),
    "dr-hoshyar": (9, "دکتر هوشیار"),
    "mehrabad-south": (9, "مهرآباد جنوبی"),

    # District 10
    "jeyhoun": (10, "جیحون"),
    "selsebil": (10, "سلسبیل"),
    "selsebil-shomali": (10, "سلسبیل"),
    "beryank": (10, "بریانک"),
    "karoon": (10, "کارون"),
    "haft-chenar": (10, "هفت‌چنار"),
    "dampezeshki": (10, "دامپزشکی"),
    "azarbaijan": (10, "آذربایجان"),
    "ghasrodasht": (10, "قصرالدشت"),

    # District 11
    "moniriyeh": (11, "منیریه"),
    "hassan-abad": (11, "حسن‌آباد"),
    "sheykh-hadi": (11, "شیخ هادی"),
    "enghelab": (11, "انقلاب"),

    # District 12
    "baharestan": (12, "بهارستان"),
    "bazaar": (12, "بازار"),
    "ferdows": (12, "فردوسی"),

    # District 13
    "piroozi": (13, "پیروزی"),
    "nirou-havayi": (13, "نیروی هوایی"),

    # District 14
    "nabard": (14, "نبرد"),
    "abouzar": (14, "ابوذر"),

    # District 15
    "afsariyeh": (15, "افسریه"),
    "moshiriyeh": (15, "مشیریه"),
    "kiyanshahr": (15, "کیانشهر"),

    # District 16
    "nazi-abad": (16, "نازی‌آباد"),
    "javadiyeh": (16, "جوادیه"),
    "yakhchi-abad": (16, "یاخچی‌آباد"),

    # District 17
    "fallah": (17, "فلاح"),
    "azari": (17, "آذری"),

    # District 18
    "shadabad": (18, "شادآباد"),
    "valiasr-town": (18, "شهرک ولیعصر"),
    "yaftabad": (18, "یافت‌آباد"),

    # District 19
    "khani-abad": (19, "خانی‌آباد"),
    "nemat-abad": (19, "نعمت‌آباد"),

    # District 20
    "shahr-e-rey": (20, "شهر ری"),
    "dolat-abad": (20, "دولت‌آباد"),

    # District 21
    "tehransar": (21, "تهرانسر"),
    "shahrak-e-azadi": (21, "شهرک آزادی"),

    # District 22
    "chitgar": (22, "چیتگر"),
    "shahrak-e-golestan": (22, "شهرک گلستان"),
    "dehkadeh-olympic": (22, "دهکده المپیک"),
    "koohak": (22, "کوهک"),
}

# Reverse lookup for neighborhoods to district candidate
_NEIGHBORHOOD_TO_DISTRICT: Dict[str, int] = {}
for dist_id, data in TEHRAN_DISTRICTS.items():
    for nh in data["neighborhoods"]:
        _NEIGHBORHOOD_TO_DISTRICT[nh] = dist_id


def suggest_district_for_neighborhood(neighborhood: Optional[str]) -> Optional[int]:
    """
    Suggest a municipal district based on neighborhood name or Divar slug.
    Does not strictly force an identity, returns None if ambiguous.
    """
    if not neighborhood:
        return None

    clean_nh = str(neighborhood).strip().lower()

    # Direct Divar slug lookup
    if clean_nh in DIVAR_SLUG_TO_DISTRICT:
        return DIVAR_SLUG_TO_DISTRICT[clean_nh][0]

    # Persian name exact match
    if clean_nh in _NEIGHBORHOOD_TO_DISTRICT:
        return _NEIGHBORHOOD_TO_DISTRICT[clean_nh]

    # Partial match check
    for nh, dist in _NEIGHBORHOOD_TO_DISTRICT.items():
        if nh in clean_nh or clean_nh in nh:
            return dist

    for slug, (dist, fa_name) in DIVAR_SLUG_TO_DISTRICT.items():
        if slug in clean_nh or clean_nh in slug or fa_name in clean_nh:
            return dist

    return None


def suggest_neighborhood_display_name(slug_or_name: Optional[str]) -> str:
    """
    Convert a Divar neighborhood slug into a clean Persian display name.
    """
    if not slug_or_name:
        return ""
    clean = str(slug_or_name).strip().lower()
    if clean in DIVAR_SLUG_TO_DISTRICT:
        return DIVAR_SLUG_TO_DISTRICT[clean][1]
    return str(slug_or_name).strip()


def get_district_coordinates(district: int) -> Tuple[float, float]:
    """
    Get center latitude and longitude for a Tehran district (1-22).
    """
    if district in TEHRAN_DISTRICTS:
        return TEHRAN_DISTRICTS[district]["center"]
    # Fallback to Tehran center
    return (35.6892, 51.3890)


def get_district_by_coordinates(lat: float, lon: float) -> Optional[int]:
    """
    Determine the municipal district (1-22) from geographic coordinates.
    """
    if not lat or not lon:
        return None
    for dist_id, data in TEHRAN_DISTRICTS.items():
        min_lat, max_lat = data["lat_range"]
        min_lon, max_lon = data["lon_range"]
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return dist_id
    return None
