"""
Persian and Arabic text, numeral, and currency normalization utilities.
"""

import re
from typing import Optional, Union

# Persian and Arabic digit translation maps
PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ENGLISH_DIGITS = "0123456789"

_DIGIT_MAP = str.maketrans(
    PERSIAN_DIGITS + ARABIC_DIGITS,
    ENGLISH_DIGITS + ENGLISH_DIGITS,
)

_TO_PERSIAN_MAP = str.maketrans(
    ENGLISH_DIGITS,
    PERSIAN_DIGITS,
)

# Persian character normalization
_CHAR_MAP = str.maketrans({
    "ي": "ی",  # Arabic Yeh to Persian Yeh
    "ك": "ک",  # Arabic Kaf to Persian Kaf
    "ة": "ه",  # Teh Marbuta to Heh
    "ۀ": "ه",
    "ؤ": "و",
    "إ": "ا",
    "أ": "ا",
    "آ": "آ",
    "ء": "",   # Hamza cleanup
})


def to_english_digits(text: Optional[Union[str, int, float]]) -> str:
    """
    Convert Persian and Arabic numerals to ASCII English numerals.
    Example: '۱۲۳۴۵' -> '12345'
    """
    if text is None:
        return ""
    return str(text).translate(_DIGIT_MAP)


def to_persian_digits(text: Optional[Union[str, int, float]]) -> str:
    """
    Convert English digits to Persian digits.
    Example: 12345 -> '۱۲۳۴۵'
    """
    if text is None:
        return ""
    return str(text).translate(_TO_PERSIAN_MAP)


def clean_persian_text(text: Optional[str]) -> str:
    """
    Clean Persian text:
    - Normalizes Arabic Yeh/Kaf to Persian
    - Cleans extra spaces and multiple ZWNJ (Zero-Width Non-Joiner)
    - Removes zero-width joiners and unexpected control characters
    """
    if not text:
        return ""

    # Normalize characters
    text = text.translate(_CHAR_MAP)

    # Convert non-breaking space and control chars
    text = text.replace("\xa0", " ")
    text = text.replace("‎", "")  # LTR mark
    text = text.replace("‏", "")  # RTL mark

    # Normalize repeated ZWNJ
    text = re.sub(r"‌{2,}", "‌", text)

    # Normalize repeated whitespaces
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def parse_iranian_price(raw_val: Union[str, int, float, None]) -> Optional[int]:
    """
    Parse any Iranian price representation into an integer of Tomans.
    Handles:
    - Raw integers or floats
    - Formatted strings: '15,000,000', '۱۵٬۰۰۰٬۰۰۰'
    - Units: '15.2 میلیارد تومان', '450 میلیون تومان', '12 میلیارد'
    - 'توافقی' or non-numeric returns None
    """
    if raw_val is None:
        return None

    if isinstance(raw_val, (int, float)):
        val = int(raw_val)
        return val if val > 0 else None

    text = str(raw_val).strip()
    if not text or "توافقی" in text or "معاوضه" in text:
        return None

    # Standardize digits and characters
    clean_str = to_english_digits(text)
    clean_str = clean_str.replace(",", "").replace("،", "").replace("٬", "")

    # Multipliers
    # میلیارد = billion = 10^9
    # میلیون = million = 10^6
    # هزار = thousand = 10^3
    multiplier = 1

    if "میلیارد" in clean_str or "billion" in clean_str.lower():
        multiplier = 1_000_000_000
    elif "میلیون" in clean_str or "million" in clean_str.lower():
        multiplier = 1_000_000
    elif "هزار" in clean_str or "thousand" in clean_str.lower():
        multiplier = 1_000

    # Extract floating point or integer number
    # Handle Persian decimal point '٫' or '.'
    clean_num_str = clean_str.replace("٫", ".")
    match = re.search(r"[-+]?\d*\.?\d+", clean_num_str)
    if not match:
        return None

    try:
        numeric_val = float(match.group(0))
        total_tomans = int(round(numeric_val * multiplier))
        # Handle rials if explicitly stated (1 Toman = 10 Rials)
        if "ریال" in clean_str:
            total_tomans = total_tomans // 10
        return total_tomans if total_tomans > 0 else None
    except (ValueError, OverflowError):
        return None


def format_toman(amount: Optional[Union[int, float]], persian_digits: bool = True) -> str:
    """
    Format a Toman amount into human-readable Iranian currency representation.
    Example:
    15_200_000_000 -> '۱۵٫۲ میلیارد تومان'
    450_000_000 -> '۴۵۰ میلیون تومان'
    """
    if amount is None or amount == 0:
        return "توافقی" if persian_digits else "Negotiable"

    amount = int(amount)
    if amount >= 1_000_000_000:
        val = amount / 1_000_000_000
        formatted = f"{val:.2f}".rstrip("0").rstrip(".") + " میلیارد تومان"
    elif amount >= 1_000_000:
        val = amount / 1_000_000
        formatted = f"{val:.1f}".rstrip("0").rstrip(".") + " میلیون تومان"
    elif amount >= 1_000:
        val = amount / 1_000
        formatted = f"{val:.0f} هزار تومان"
    else:
        formatted = f"{amount:,} تومان"

    if persian_digits:
        return to_persian_digits(formatted).replace(".", "٫")
    return formatted
