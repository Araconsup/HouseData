"""
Tests for PWA (Progressive Web App) Manifest, Service Worker, Icons, and Vercel WSGI entrypoint.
"""

import json
from pathlib import Path
import pytest
from django.conf import settings
from django.test import Client


def test_pwa_manifest_endpoint():
    client = Client()
    res = client.get("/manifest.json")
    assert res.status_code == 200
    assert "application/manifest+json" in res["Content-Type"]

    data = json.loads(b"".join(res.streaming_content).decode("utf-8"))
    assert data["short_name"] == "HOUSEDATA"
    assert data["display"] == "standalone"
    assert data["start_url"] == "/"
    assert len(data["icons"]) >= 2


def test_service_worker_endpoint():
    client = Client()
    res = client.get("/sw.js")
    assert res.status_code == 200
    assert "javascript" in res["Content-Type"]
    assert res.headers.get("Service-Worker-Allowed") == "/"

    content = b"".join(res.streaming_content).decode("utf-8")
    assert "housedata-pwa-v1" in content
    assert "addEventListener('fetch'" in content


def test_pwa_icons_exist():
    base_dir = settings.BASE_DIR
    icon_svg = base_dir / "static/img/icon.svg"
    icon_192 = base_dir / "static/img/icon-192.png"
    icon_512 = base_dir / "static/img/icon-512.png"

    assert icon_svg.exists() and icon_svg.stat().st_size > 100
    assert icon_192.exists() and icon_192.stat().st_size > 100
    assert icon_512.exists() and icon_512.stat().st_size > 100


def test_vercel_wsgi_app():
    from housedata.wsgi import app, application
    assert app is not None
    assert app == application
    assert callable(app)


def test_vercel_json_configuration():
    base_dir = settings.BASE_DIR
    vercel_path = base_dir / "vercel.json"
    assert vercel_path.exists()

    with open(vercel_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    assert config.get("version") == 2
    assert any(b.get("src") == "housedata/wsgi.py" for b in config.get("builds", []))
    assert any(r.get("src") == "/manifest.json" for r in config.get("routes", []))
    assert any(r.get("src") == "/sw.js" for r in config.get("routes", []))
