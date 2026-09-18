"""
Official Divar Kenar Open API Client.
Implements request safety, quota accounting, retries with exponential backoff,
circuit breaker, and mock responses for local testing.
"""

import logging
import math
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from django.conf import settings
from django.utils import timezone as django_tz

logger = logging.getLogger(__name__)


class DivarApiError(Exception):
    """Base exception for Divar API failures."""
    pass


class DivarQuotaExceededError(DivarApiError):
    """Raised when configured request budget is exceeded."""
    pass


class DivarCircuitBreakerOpenError(DivarApiError):
    """Raised when circuit breaker is tripped due to consecutive failures."""
    pass


class CircuitBreaker:
    """In-memory circuit breaker to protect against hammering a failing API."""
    def __init__(self, failure_threshold: int = 5, recovery_timeout_sec: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_sec = recovery_timeout_sec
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Divar API Circuit Breaker tripped OPEN ({self.failure_count} consecutive failures). "
                f"Cooldown: {self.recovery_timeout_sec}s"
            )

    def can_request(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if self.last_failure_time and (time.time() - self.last_failure_time > self.recovery_timeout_sec):
                self.state = "HALF_OPEN"
                logger.info("Divar API Circuit Breaker transitioned to HALF_OPEN")
                return True
            return False
        if self.state == "HALF_OPEN":
            return True
        return False


class DivarApiClient:
    """
    Official Divar Kenar API Client.
    Search endpoint: POST https://open-api.divar.ir/v2/open-platform/finder/post
    Listing endpoint: GET https://open-api.divar.ir/v1/open-platform/finder/post/{token}
    """

    SEARCH_ENDPOINT = "https://open-api.divar.ir/v2/open-platform/finder/post"
    GET_POST_ENDPOINT = "https://open-api.divar.ir/v1/open-platform/finder/post/{token}"

    _circuit_breaker = CircuitBreaker()
    _last_request_time = 0.0

    def __init__(self, api_key: Optional[str] = None, timeout: int = 15):
        self.api_key = api_key if api_key is not None else getattr(settings, "DIVAR_API_KEY", "")
        self.timeout = timeout
        self.min_request_interval = getattr(settings, "DIVAR_REQUEST_INTERVAL_SEC", 0.5)
        self.daily_quota = getattr(settings, "DIVAR_DAILY_REQUEST_LIMIT", 5000)
        self.mock_mode = getattr(settings, "MOCK_DIVAR_API", False) or not self.api_key

    def _throttle(self):
        """Enforce minimum interval between consecutive outbound requests."""
        elapsed = time.time() - self.__class__._last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.__class__._last_request_time = time.time()

    def _check_daily_quota(self):
        """Check if today's API request quota has been exhausted."""
        from ingestion.models import ApiRequestLog
        today_start = django_tz.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = ApiRequestLog.objects.filter(request_time__gte=today_start).count()
        if count >= self.daily_quota:
            raise DivarQuotaExceededError(
                f"Configured Divar API request budget ({self.daily_quota}/day) reached today ({count} used)."
            )

    def search_posts(
        self,
        city: str = "tehran",
        category: str = "apartment-sale",
        district: Optional[int] = None,
        neighborhood: Optional[str] = None,
        min_area: Optional[int] = None,
        max_area: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_rooms: Optional[int] = None,
        max_rooms: Optional[int] = None,
        only_with_parking: bool = False,
        only_with_elevator: bool = False,
        partition_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search listings using Divar Kenar Open Platform search endpoint.
        Returns up to 100 listings per request (API constraint).
        """
        if self.mock_mode:
            logger.info("Using Mock Divar API Generator for search")
            return self._generate_mock_search_results(
                city=city,
                category=category,
                district=district,
                neighborhood=neighborhood,
                min_area=min_area,
                max_area=max_area,
                min_price=min_price,
                max_price=max_price,
                min_rooms=min_rooms,
                max_rooms=max_rooms,
                only_with_parking=only_with_parking,
                only_with_elevator=only_with_elevator,
            )

        if not self._circuit_breaker.can_request():
            raise DivarCircuitBreakerOpenError("Circuit breaker is currently OPEN due to previous API failures.")

        self._check_daily_quota()
        self._throttle()

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "HOUSEDATA-Tehran-RealEstate/1.0",
        }

        # Build official Divar finder payload
        # Note: city must always be tehran for our application
        from core.constants import CANONICAL_TO_DIVAR_CATEGORY
        divar_cat = CANONICAL_TO_DIVAR_CATEGORY.get(category, category)

        payload: Dict[str, Any] = {
            "city": city.lower() or "tehran",
        }
        if divar_cat:
            payload["category"] = divar_cat

        query_dict = {}
        if min_area or max_area:
            query_dict["size"] = {}
            if min_area:
                query_dict["size"]["min"] = min_area
            if max_area:
                query_dict["size"]["max"] = max_area
        if min_price or max_price:
            query_dict["price"] = {}
            if min_price:
                query_dict["price"]["min"] = min_price
            if max_price:
                query_dict["price"]["max"] = max_price
        if min_rooms or max_rooms:
            query_dict["rooms"] = {}
            if min_rooms:
                query_dict["rooms"]["min"] = min_rooms
            if max_rooms:
                query_dict["rooms"]["max"] = max_rooms
        if only_with_parking:
            query_dict["parking"] = True
        if only_with_elevator:
            query_dict["elevator"] = True

        if query_dict:
            payload["query"] = query_dict

        start_t = time.time()
        http_status = None
        error_msg = ""
        results_count = 0
        request_id = ""

        # Retry loop for transient 5xx/network errors
        max_retries = 3
        last_exception = None

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.SEARCH_ENDPOINT,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                http_status = response.status_code
                request_id = response.headers.get("x-request-id", "")

                if response.status_code == 200:
                    data = response.json()
                    posts = data.get("posts", [])
                    results_count = len(posts)
                    self._circuit_breaker.record_success()
                    self._log_request(
                        endpoint=self.SEARCH_ENDPOINT,
                        partition_id=partition_id,
                        http_status=http_status,
                        duration_ms=int((time.time() - start_t) * 1000),
                        results_count=results_count,
                        request_id=request_id,
                    )
                    return posts

                # 4xx client errors should not retry
                if 400 <= response.status_code < 500:
                    error_msg = f"Client error {response.status_code}: {response.text[:200]}"
                    self._circuit_breaker.record_failure()
                    break

                # 5xx server errors retry
                error_msg = f"Server error {response.status_code}: {response.text[:200]}"
                time.sleep(2 ** attempt)

            except requests.RequestException as exc:
                last_exception = exc
                error_msg = str(exc)
                time.sleep(2 ** attempt)

        self._circuit_breaker.record_failure()
        duration_ms = int((time.time() - start_t) * 1000)
        self._log_request(
            endpoint=self.SEARCH_ENDPOINT,
            partition_id=partition_id,
            http_status=http_status,
            duration_ms=duration_ms,
            results_count=0,
            error=error_msg,
            request_id=request_id,
        )

        raise DivarApiError(f"Divar search request failed: {error_msg} (Last exception: {last_exception})")

    def get_post_details(self, token: str) -> Dict[str, Any]:
        """
        Fetch full details of a single post by token.
        GET https://open-api.divar.ir/v1/open-platform/finder/post/{token}
        """
        if self.mock_mode:
            return self._generate_mock_post_detail(token)

        if not self._circuit_breaker.can_request():
            raise DivarCircuitBreakerOpenError("Circuit breaker is currently OPEN.")

        self._check_daily_quota()
        self._throttle()

        url = self.GET_POST_ENDPOINT.format(token=token)
        headers = {
            "x-api-key": self.api_key,
            "User-Agent": "HOUSEDATA-Tehran-RealEstate/1.0",
        }

        start_t = time.time()
        http_status = None
        error_msg = ""
        request_id = ""

        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
            http_status = response.status_code
            request_id = response.headers.get("x-request-id", "")

            if response.status_code == 200:
                self._circuit_breaker.record_success()
                data = response.json()
                self._log_request(
                    endpoint=url,
                    partition_id=None,
                    http_status=http_status,
                    duration_ms=int((time.time() - start_t) * 1000),
                    results_count=1,
                    request_id=request_id,
                )
                return data

            error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
            self._circuit_breaker.record_failure()
        except requests.RequestException as exc:
            error_msg = str(exc)
            self._circuit_breaker.record_failure()

        duration_ms = int((time.time() - start_t) * 1000)
        self._log_request(
            endpoint=url,
            partition_id=None,
            http_status=http_status,
            duration_ms=duration_ms,
            results_count=0,
            error=error_msg,
            request_id=request_id,
        )
        raise DivarApiError(f"Failed to fetch Divar post details for {token}: {error_msg}")

    def _log_request(
        self,
        endpoint: str,
        partition_id: Optional[int],
        http_status: Optional[int],
        duration_ms: int,
        results_count: int,
        error: str = "",
        request_id: str = "",
    ):
        """Save an audit record of the API request to ApiRequestLog."""
        try:
            from ingestion.models import ApiRequestLog, SearchPartition
            partition = SearchPartition.objects.filter(id=partition_id).first() if partition_id else None
            ApiRequestLog.objects.create(
                endpoint=endpoint,
                partition=partition,
                http_status=http_status,
                response_time_ms=duration_ms,
                number_of_results=results_count,
                error=error,
                request_id=request_id,
            )
        except Exception as e:
            logger.error(f"Failed to write ApiRequestLog: {e}")

    # =========================================================================
    # Mock Response Generator (for Testing, CI, and Development)
    # =========================================================================
    def _generate_mock_search_results(
        self,
        city: str = "tehran",
        category: str = "apartment-sale",
        district: Optional[int] = None,
        neighborhood: Optional[str] = None,
        min_area: Optional[int] = None,
        max_area: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_rooms: Optional[int] = None,
        max_rooms: Optional[int] = None,
        only_with_parking: bool = False,
        only_with_elevator: bool = False,
        count: int = 15,
    ) -> List[Dict[str, Any]]:
        """Generate realistic mock Divar search posts matching query parameters."""
        from core.tehran_data import TEHRAN_DISTRICTS

        target_district = district or random.choice(list(TEHRAN_DISTRICTS.keys()))
        dist_info = TEHRAN_DISTRICTS.get(target_district, TEHRAN_DISTRICTS[1])
        neighborhoods = dist_info["neighborhoods"]
        target_nh = neighborhood or random.choice(neighborhoods)

        is_rent = "rent" in category

        posts = []
        for i in range(count):
            token = f"mock_{target_district}_{int(time.time())}_{i}_{random.randint(1000, 9999)}"

            # Realistic area
            low_area = min_area or 50
            high_area = max_area or 160
            area = random.randint(low_area, high_area)

            # Realistic rooms
            if min_rooms is not None and max_rooms is not None:
                rooms = random.randint(min_rooms, max_rooms)
            elif area < 65:
                rooms = 1
            elif area < 110:
                rooms = 2
            elif area < 180:
                rooms = 3
            else:
                rooms = 4

            # Price modeling based on Tehran district tiers
            # Tier 1 (Districts 1, 2, 3): 140M - 350M Toman / m2
            # Tier 2 (Districts 5, 6, 7): 90M - 180M Toman / m2
            # Tier 3 (Districts 4, 8, 22): 70M - 130M Toman / m2
            # Tier 4 (Districts 9-14): 50M - 90M Toman / m2
            # Tier 5 (Districts 15-20): 35M - 65M Toman / m2
            if target_district in (1, 2, 3):
                base_sqm = random.randint(150_000_000, 320_000_000)
            elif target_district in (5, 6, 7):
                base_sqm = random.randint(95_000_000, 175_000_000)
            elif target_district in (4, 8, 22):
                base_sqm = random.randint(75_000_000, 130_000_000)
            elif target_district in (9, 10, 11, 12, 13, 14):
                base_sqm = random.randint(52_000_000, 90_000_000)
            else:
                base_sqm = random.randint(35_000_000, 65_000_000)

            # Occasional anomaly listing for testing detection
            if i == 0 and not is_rent:
                # 35% below market price
                base_sqm = int(base_sqm * 0.65)

            total_sale_price = base_sqm * area
            deposit = int(base_sqm * area * 0.15) if is_rent else None
            monthly_rent = int(deposit * 0.025) if is_rent else None

            # Coordinates with slight random jitter within district bounds
            lat_c, lon_c = dist_info["center"]
            lat = lat_c + random.uniform(-0.015, 0.015)
            lon = lon_c + random.uniform(-0.015, 0.015)

            age = random.randint(0, 25)
            floor = random.randint(1, 8)
            total_floors = floor + random.randint(0, 3)

            parking = True if only_with_parking else (random.random() > 0.15)
            elevator = True if only_with_elevator else (random.random() > 0.20 if total_floors > 3 else False)
            storage = random.random() > 0.10

            title = f"آپارتمان {area} متری {rooms} خوابه در {target_nh}" if "apartment" in category else f"ملک {area} متری در {target_nh}"

            post_data = {
                "token": token,
                "title": title,
                "category": category,
                "city": city,
                "district": target_district,
                "neighborhood": target_nh,
                "area_m2": area,
                "rooms": rooms,
                "floor": floor,
                "total_floors": total_floors,
                "building_age": age,
                "parking": parking,
                "elevator": elevator,
                "storage": storage,
                "balcony": True,
                "latitude": round(lat, 5),
                "longitude": round(lon, 5),
                "price": None if is_rent else total_sale_price,
                "deposit": deposit,
                "rent": monthly_rent,
                "published_at": django_tz.now().isoformat(),
                "description": f"{title} با نورگیر عالی، دسترسی مناسب، سند تک‌برگ و متریال درجه یک.",
            }
            posts.append(post_data)

        return posts

    def _generate_mock_post_detail(self, token: str) -> Dict[str, Any]:
        """Generate mock post detail matching Divar Kenar v1 get_post schema."""
        return {
            "token": token,
            "data": {
                "title": f"ملک در تهران - کد {token[-6:]}",
                "description": "واحد بسیار تمیز و خوش‌نقشه در محیطی آرام با کلیه امکانات رفاهی.",
                "category": "apartment-sale",
                "city": "tehran",
                "web_widgets": {
                    "header": {"title": "آپارتمان خوش‌نقشه در تهران"},
                    "list_data": [
                        {"title": "متراژ", "value": "100"},
                        {"title": "ساخت", "value": "1398"},
                        {"title": "اتاق", "value": "2"},
                        {"title": "قیمت کل", "value": "12,000,000,000 تومان"},
                        {"title": "قیمت هر متر", "value": "120,000,000 تومان"},
                        {"title": "پارکینگ", "value": "دارد"},
                        {"title": "آسانسور", "value": "دارد"},
                        {"title": "انباری", "value": "دارد"},
                    ]
                }
            }
        }
