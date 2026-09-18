"""
Tests for Frontend Template Rendering and HTTP 200 responses.
"""

import pytest
from django.test import Client
from core.constants import CATEGORY_APARTMENT_SALE
from listings.models import DivarListing


@pytest.fixture
def sample_listing_for_view(db):
    return DivarListing.objects.create(
        divar_token="view_test_tok_001",
        title="آپارتمان آزمایشی نیاوران",
        category=CATEGORY_APARTMENT_SALE,
        district=1,
        neighborhood="نیاوران",
        area_m2=120,
        price=24_000_000_000,
        price_per_m2=200_000_000,
        rooms=3,
        parking=True,
        elevator=True,
    )


@pytest.mark.django_db
def test_frontend_pages_render(sample_listing_for_view):
    client = Client()

    # 1. Dashboard
    res = client.get("/")
    assert res.status_code == 200
    assert "داشبورد بازار مسکن تهران" in res.content.decode("utf-8")

    # 2. Listings catalog
    res = client.get("/listings/")
    assert res.status_code == 200
    assert "فهرست و کاوشگر املاک تهران" in res.content.decode("utf-8")

    # 3. Listing detail
    res = client.get(f"/listings/{sample_listing_for_view.divar_token}/")
    assert res.status_code == 200
    assert "مشخصات اصلی ملک" in res.content.decode("utf-8")
    assert "تحلیل املاک مشابه" in res.content.decode("utf-8")

    # 4. Map page
    res = client.get("/map/")
    assert res.status_code == 200
    assert "نقشه تعاملی مسکن تهران" in res.content.decode("utf-8")

    # 5. Anomalies page
    res = client.get("/anomalies/")
    assert res.status_code == 200
    assert "کاوشگر املاک نامتعارف آماری" in res.content.decode("utf-8")

    # 6. Statistics page
    res = client.get("/statistics/")
    assert res.status_code == 200
    assert "شاخص‌های جامع آماری بازار مسکن تهران" in res.content.decode("utf-8")

    # 7. Collection management page
    res = client.get("/collection/")
    assert res.status_code == 200
    assert "مدیریت جمع‌آوری داده و پوشش API دیوار" in res.content.decode("utf-8")

    # 8. Admin alias
    res = client.get("/admin/data-collection/")
    assert res.status_code == 200
