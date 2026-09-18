"""
Constants for HOUSEDATA system.
"""

# Supported Property Categories
CATEGORY_APARTMENT_SALE = "apartment-sale"
CATEGORY_HOUSE_VILLA_SALE = "house-villa-sale"
CATEGORY_LAND_SALE = "land-sale"
CATEGORY_COMMERCIAL_SALE = "commercial-sale"

CATEGORY_APARTMENT_RENT = "apartment-rent"
CATEGORY_HOUSE_VILLA_RENT = "house-villa-rent"
CATEGORY_COMMERCIAL_RENT = "commercial-rent"

SALE_CATEGORIES = [
    CATEGORY_APARTMENT_SALE,
    CATEGORY_HOUSE_VILLA_SALE,
    CATEGORY_LAND_SALE,
    CATEGORY_COMMERCIAL_SALE,
]

RENT_CATEGORIES = [
    CATEGORY_APARTMENT_RENT,
    CATEGORY_HOUSE_VILLA_RENT,
    CATEGORY_COMMERCIAL_RENT,
]

ALL_CATEGORIES = SALE_CATEGORIES + RENT_CATEGORIES

# Divar Kenar Open API Category Mapping
DIVAR_TO_CANONICAL_CATEGORY = {
    "apartment-sell": CATEGORY_APARTMENT_SALE,
    "apartment-sale": CATEGORY_APARTMENT_SALE,
    "house-villa-sell": CATEGORY_HOUSE_VILLA_SALE,
    "house-villa-sale": CATEGORY_HOUSE_VILLA_SALE,
    "plot-old": CATEGORY_LAND_SALE,
    "land-sale": CATEGORY_LAND_SALE,
    "commercial-sell": CATEGORY_COMMERCIAL_SALE,
    "commercial-sale": CATEGORY_COMMERCIAL_SALE,
    "apartment-rent": CATEGORY_APARTMENT_RENT,
    "house-villa-rent": CATEGORY_HOUSE_VILLA_RENT,
    "commercial-rent": CATEGORY_COMMERCIAL_RENT,
}

CANONICAL_TO_DIVAR_CATEGORY = {
    CATEGORY_APARTMENT_SALE: "apartment-sell",
    CATEGORY_HOUSE_VILLA_SALE: "house-villa-sell",
    CATEGORY_LAND_SALE: "plot-old",
    CATEGORY_COMMERCIAL_SALE: "commercial-sell",
    CATEGORY_APARTMENT_RENT: "apartment-rent",
    CATEGORY_HOUSE_VILLA_RENT: "house-villa-rent",
    CATEGORY_COMMERCIAL_RENT: "commercial-rent",
}

CATEGORY_CHOICES = [
    (CATEGORY_APARTMENT_SALE, "Apartment Sale / فروش آپارتمان"),
    (CATEGORY_HOUSE_VILLA_SALE, "House & Villa Sale / فروش خانه و ویلا"),
    (CATEGORY_LAND_SALE, "Land & Plot Sale / فروش زمین و کلنگی"),
    (CATEGORY_COMMERCIAL_SALE, "Commercial Sale / فروش اداری و تجاری"),
    (CATEGORY_APARTMENT_RENT, "Apartment Rent / رهن و اجاره آپارتمان"),
    (CATEGORY_HOUSE_VILLA_RENT, "House & Villa Rent / رهن و اجاره خانه و ویلا"),
    (CATEGORY_COMMERCIAL_RENT, "Commercial Rent / رهن و اجاره اداری و تجاری"),
]

# Area Buckets for Coverage Segmentation
AREA_BUCKETS = [
    {"name": "0-50 m²", "slug": "0-50", "min_area": 0, "max_area": 50},
    {"name": "50-70 m²", "slug": "50-70", "min_area": 50, "max_area": 70},
    {"name": "70-90 m²", "slug": "70-90", "min_area": 70, "max_area": 90},
    {"name": "90-120 m²", "slug": "90-120", "min_area": 90, "max_area": 120},
    {"name": "120-160 m²", "slug": "120-160", "min_area": 120, "max_area": 160},
    {"name": "160-220 m²", "slug": "160-220", "min_area": 160, "max_area": 220},
    {"name": "220+ m²", "slug": "220-plus", "min_area": 220, "max_area": None},
]

# Statistical and Anomaly Thresholds
MIN_COMPARABLE_SAMPLE_SIZE = 15

CONFIDENCE_STRONG = "strong"
CONFIDENCE_MODERATE = "moderate"
CONFIDENCE_WEAK = "weak"
CONFIDENCE_INSUFFICIENT = "insufficient_data"

CONFIDENCE_CHOICES = [
    (CONFIDENCE_STRONG, "Strong Evidence / شواهد قوی"),
    (CONFIDENCE_MODERATE, "Moderate Evidence / شواهد متوسط"),
    (CONFIDENCE_WEAK, "Weak Evidence / شواهد ضعیف"),
    (CONFIDENCE_INSUFFICIENT, "Insufficient Data / داده ناکافی"),
]

# Price History Event Types
EVENT_INITIAL = "initial"
EVENT_PRICE_INCREASE = "price_increase"
EVENT_PRICE_DECREASE = "price_decrease"
EVENT_UNCHANGED = "unchanged"
EVENT_AREA_CHANGE = "area_change"
EVENT_TITLE_MODIFICATION = "title_modification"
EVENT_DISAPPEARED = "disappeared"
EVENT_REAPPEARED = "reappeared"
