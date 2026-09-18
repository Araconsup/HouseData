"""
Tests for Persian and Arabic numeral conversion, text cleaning, and price normalization.
"""

import pytest
from core.normalizers import (
    clean_persian_text,
    format_toman,
    parse_iranian_price,
    to_english_digits,
    to_persian_digits,
)


def test_to_english_digits():
    assert to_english_digits("۱۲۳۴۵۶۷۸۹۰") == "1234567890"
    assert to_english_digits("١٢٣٤٥٦٧٨٩٠") == "1234567890"
    assert to_english_digits("آپارتمان ۱۲۰ متری") == "آپارتمان 120 متری"
    assert to_english_digits(None) == ""
    assert to_english_digits(12345) == "12345"


def test_to_persian_digits():
    assert to_persian_digits("1234567890") == "۱۲۳۴۵۶۷۸۹۰"
    assert to_persian_digits(450) == "۴۵۰"
    assert to_persian_digits(None) == ""


def test_clean_persian_text():
    # Normalizes Arabic Yeh/Kaf to Persian
    raw = "املاك تهراني با قيمت مناسب"
    cleaned = clean_persian_text(raw)
    assert "ی" in cleaned and "ي" not in cleaned
    assert "ک" in cleaned and "ك" not in cleaned

    # Normalizes duplicate ZWNJ and excessive whitespace
    raw_zwnj = "سعادت‌‌‌‌آباد   تهران\n\n\n\nبسیار تمیز"
    cleaned_zwnj = clean_persian_text(raw_zwnj)
    assert "  " not in cleaned_zwnj
    assert "\n\n\n" not in cleaned_zwnj


def test_parse_iranian_price():
    # Direct numbers
    assert parse_iranian_price(15_000_000_000) == 15_000_000_000

    # Formatted comma strings
    assert parse_iranian_price("15,200,000,000") == 15_200_000_000
    assert parse_iranian_price("۱۵٬۲۰۰٬۰۰۰٬۰۰۰") == 15_200_000_000

    # Billions (میلیارد تومان)
    assert parse_iranian_price("15.2 میلیارد تومان") == 15_200_000_000
    assert parse_iranian_price("۱۵٫۲ میلیارد تومان") == 15_200_000_000
    assert parse_iranian_price("12 میلیارد") == 12_000_000_000

    # Millions (میلیون تومان)
    assert parse_iranian_price("450 میلیون تومان") == 450_000_000
    assert parse_iranian_price("۴۵۰ میلیون") == 450_000_000

    # Non-numeric / agreement strings return None
    assert parse_iranian_price("توافقی") is None
    assert parse_iranian_price("قیمت توافقی") is None
    assert parse_iranian_price(None) is None
    assert parse_iranian_price(0) is None
    assert parse_iranian_price(-1000) is None


def test_format_toman():
    assert "میلیارد" in format_toman(15_200_000_000, persian_digits=True)
    assert "میلیون" in format_toman(450_000_000, persian_digits=True)
    assert format_toman(None) == "توافقی"
    assert format_toman(0) == "توافقی"
