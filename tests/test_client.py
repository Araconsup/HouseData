"""
Tests for Divar Kenar Open API Client, authentication headers, error handling,
circuit breaker, and mock responses.
"""

from unittest.mock import MagicMock, patch
import pytest
import requests
from ingestion.client import (
    CircuitBreaker,
    DivarApiClient,
    DivarApiError,
    DivarCircuitBreakerOpenError,
    DivarQuotaExceededError,
)


def test_client_headers():
    client = DivarApiClient(api_key="test-divar-secret-key-123")
    assert client.api_key == "test-divar-secret-key-123"


def test_circuit_breaker_transition():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout_sec=10.0)
    assert cb.state == "CLOSED"
    assert cb.can_request() is True

    cb.record_failure()
    cb.record_failure()
    assert cb.state == "CLOSED"
    assert cb.can_request() is True

    cb.record_failure()
    assert cb.state == "OPEN"
    assert cb.can_request() is False

    cb.record_success()
    assert cb.state == "CLOSED"
    assert cb.can_request() is True


def test_mock_search_results():
    client = DivarApiClient(api_key="")
    assert client.mock_mode is True

    posts = client.search_posts(
        city="tehran",
        category="apartment-sale",
        district=2,
        min_area=80,
        max_area=120,
    )

    assert len(posts) > 0
    first = posts[0]
    assert "token" in first
    assert "title" in first
    assert first["district"] == 2
    assert 80 <= first["area_m2"] <= 120
    assert first["city"] == "tehran"
    assert first["price"] is not None
    assert first["price"] > 0


@pytest.mark.django_db
@patch("requests.post")
def test_real_client_auth_header_and_search(mock_post):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"x-request-id": "req-999"}
    mock_response.json.return_value = {
        "posts": [
            {"token": "divar_token_abc", "title": "آپارتمان در سعادت‌آباد", "area_m2": 100, "price": 10000000000}
        ]
    }
    mock_post.return_value = mock_response

    client = DivarApiClient(api_key="test-api-key")
    client.mock_mode = False  # force real HTTP path

    results = client.search_posts(city="tehran", category="apartment-sale", district=2)
    assert len(results) == 1
    assert results[0]["token"] == "divar_token_abc"

    # Verify headers sent
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    headers = call_args[1]["headers"]
    assert headers["x-api-key"] == "test-api-key"
    assert "application/json" in headers["Content-Type"]


@pytest.mark.django_db
@patch("time.sleep")
@patch("requests.post")
def test_client_retry_and_circuit_breaker(mock_post, mock_sleep):
    mock_post.side_effect = requests.RequestException("Network connection failed")

    client = DivarApiClient(api_key="test-api-key")
    client.mock_mode = False
    client._circuit_breaker = CircuitBreaker(failure_threshold=2)

    with pytest.raises(DivarApiError):
        client.search_posts(city="tehran", category="apartment-sale")

    # Second failure should trip circuit breaker
    with pytest.raises(DivarApiError):
        client.search_posts(city="tehran", category="apartment-sale")

    # Third call should immediately raise DivarCircuitBreakerOpenError without network call
    with pytest.raises(DivarCircuitBreakerOpenError):
        client.search_posts(city="tehran", category="apartment-sale")


@pytest.mark.django_db
@patch("time.sleep")
@patch("requests.post")
def test_client_429_rate_limit_retry_and_backoff(mock_post, mock_sleep):
    # First returns 429 with Retry-After: 3, then succeeds with 200
    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.headers = {"Retry-After": "3"}

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.headers = {}
    resp_200.json.return_value = {"posts": [{"token": "post_after_retry", "title": "ملک بعد از انتظار"}]}

    mock_post.side_effect = [resp_429, resp_200]

    client = DivarApiClient(api_key="test-api-key")
    client.mock_mode = False

    posts = client.search_posts(city="tehran", category="apartment-sale")
    assert len(posts) == 1
    assert posts[0]["token"] == "post_after_retry"
    mock_sleep.assert_any_call(3)
