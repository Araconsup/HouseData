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
            "مرزداران", "شهرآرا", "تهران‌ویلا", "طرشت", "توحید", "پونک (جنوبی)",
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
            "بریانک", "سلسبیل", "کارون", "جیحون", "هفت‌چنار", "دامپزشکی",
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

# Reverse lookup for neighborhoods to district candidate
_NEIGHBORHOOD_TO_DISTRICT: Dict[str, int] = {}
for dist_id, data in TEHRAN_DISTRICTS.items():
    for nh in data["neighborhoods"]:
        _NEIGHBORHOOD_TO_DISTRICT[nh] = dist_id


def suggest_district_for_neighborhood(neighborhood: Optional[str]) -> Optional[int]:
    """
    Suggest a municipal district based on neighborhood name.
    Does not strictly force an identity, returns None if ambiguous.
    """
    if not neighborhood:
        return None

    clean_nh = neighborhood.strip()
    if clean_nh in _NEIGHBORHOOD_TO_DISTRICT:
        return _NEIGHBORHOOD_TO_DISTRICT[clean_nh]

    # Partial match check
    for nh, dist in _NEIGHBORHOOD_TO_DISTRICT.items():
        if nh in clean_nh or clean_nh in nh:
            return dist

    return None


def get_district_coordinates(district: int) -> Tuple[float, float]:
    """
    Get center latitude and longitude for a Tehran district (1-22).
    """
    if district in TEHRAN_DISTRICTS:
        return TEHRAN_DISTRICTS[district]["center"]
    # Fallback to Tehran center
    return (35.6892, 51.3890)
