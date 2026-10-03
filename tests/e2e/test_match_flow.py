from __future__ import annotations

import json
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from PIL import Image
from playwright.sync_api import Page, expect
import pytest


class StaticHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, static_root: Path, **kwargs: Any) -> None:
        self.static_root = static_root
        super().__init__(*args, directory=str(static_root), **kwargs)

    def translate_path(self, path: str) -> str:
        request_path = urlsplit(path).path
        if request_path == "/":
            return str(self.static_root / "index.html")
        if request_path.startswith("/static/"):
            candidate = (self.static_root / unquote(request_path.removeprefix("/static/"))).resolve()
            try:
                candidate.relative_to(self.static_root.resolve())
            except ValueError:
                return str(self.static_root / "not-found")
            return str(candidate)
        return str(self.static_root / "not-found")

    def log_message(self, format_string: str, *args: Any) -> None:
        return


@pytest.fixture

def static_site_url() -> Any:
    static_root = Path(__file__).parents[2] / "src" / "dog_match" / "static"
    handler = partial(StaticHandler, static_root=static_root)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def test_user_can_upload_photo_and_read_match_on_mobile_and_desktop(page: Page, static_site_url: str) -> None:
    image_bytes = bytearray()
    image = Image.new("RGB", (12, 12), (40, 120, 50))
    from io import BytesIO

    output = BytesIO()
    image.save(output, format="JPEG")
    image.close()
    image_bytes.extend(output.getvalue())
    reference_bytes = bytes(image_bytes)

    page.route(
        "**/api/v1/matches",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "breed_name": "border collie dog",
                    "similarity_percent": 87,
                    "reference_image_url": "/api/v1/reference-images/opaque-id",
                    "disclaimer": "Closest visual match, not a guaranteed breed identification.",
                }
            ),
        ),
    )
    page.route(
        "**/api/v1/reference-images/*",
        lambda route: route.fulfill(status=200, content_type="image/jpeg", body=reference_bytes),
    )
    page.goto(static_site_url)
    page.get_by_label("Your dog's photo").set_input_files(
        {"name": "dog.jpg", "mimeType": "image/jpeg", "buffer": reference_bytes}
    )
    page.get_by_role("button", name="Find a breed match").click()
    expect(page.locator("#breed-name")).to_have_text("border collie dog")
    expect(page.locator("#similarity-score")).to_have_text("87%")
    expect(page.locator("#reference-image")).to_be_visible()

    for width, height in ((390, 844), (768, 1024), (1365, 900)):
        page.set_viewport_size({"width": width, "height": height})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")


def test_failed_match_shows_recovery_message_and_allows_retry(page: Page, static_site_url: str) -> None:
    image = Image.new("RGB", (12, 12), (40, 120, 50))
    from io import BytesIO

    output = BytesIO()
    image.save(output, format="JPEG")
    image.close()
    image_bytes = output.getvalue()
    request_count = 0

    def respond_to_match(route: Any) -> None:
        nonlocal request_count
        request_count += 1
        if request_count == 1:
            route.fulfill(
                status=415,
                content_type="application/json",
                body=json.dumps({"error": {"code": "invalid_jpeg", "message": "Choose a readable JPG photo."}}),
            )
            return
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "breed_name": "beagle dog",
                    "similarity_percent": 72,
                    "reference_image_url": "/api/v1/reference-images/retry-id",
                    "disclaimer": "Closest visual match, not a guaranteed breed identification.",
                }
            ),
        )

    page.route("**/api/v1/matches", respond_to_match)
    page.route(
        "**/api/v1/reference-images/*",
        lambda route: route.fulfill(status=200, content_type="image/jpeg", body=image_bytes),
    )
    page.goto(static_site_url)
    page.get_by_label("Your dog's photo").set_input_files(
        {"name": "dog.jpg", "mimeType": "image/jpeg", "buffer": image_bytes}
    )
    page.get_by_role("button", name="Find a breed match").click()
    expect(page.locator("#error-message")).to_contain_text("Choose a readable JPG photo")
    expect(page.locator("#result-panel")).to_be_hidden()

    page.get_by_role("button", name="Find a breed match").click()
    expect(page.locator("#breed-name")).to_have_text("beagle dog")
    assert request_count == 2


def test_upload_and_submit_controls_are_keyboard_operable(page: Page, static_site_url: str) -> None:
    image = Image.new("RGB", (12, 12), (45, 100, 55))
    from io import BytesIO

    output = BytesIO()
    image.save(output, format="JPEG")
    image.close()
    image_bytes = output.getvalue()
    page.route(
        "**/api/v1/matches",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(
                {
                    "breed_name": "spaniel dog",
                    "similarity_percent": 64,
                    "reference_image_url": "/api/v1/reference-images/keyboard-id",
                    "disclaimer": "Closest visual match, not a guaranteed breed identification.",
                }
            ),
        ),
    )
    page.route(
        "**/api/v1/reference-images/*",
        lambda route: route.fulfill(status=200, content_type="image/jpeg", body=image_bytes),
    )
    page.goto(static_site_url)

    photo_control = page.get_by_label("Your dog's photo")
    for _ in range(5):
        if photo_control.evaluate("element => element === document.activeElement"):
            break
        page.keyboard.press("Tab")
    expect(photo_control).to_be_focused()
    page.get_by_label("Your dog's photo").set_input_files(
        {"name": "dog.jpg", "mimeType": "image/jpeg", "buffer": image_bytes}
    )
    page.keyboard.press("Tab")
    expect(page.get_by_role("button", name="Find a breed match")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page.locator("#breed-name")).to_have_text("spaniel dog")


def test_upload_control_is_ready_within_five_seconds_on_broadband(page: Page, static_site_url: str) -> None:
    if page.context.browser is None or page.context.browser.browser_type.name != "chromium":
        pytest.skip("Network emulation uses Chromium DevTools Protocol")
    session = page.context.new_cdp_session(page)
    session.send("Network.enable")
    session.send(
        "Network.emulateNetworkConditions",
        {
            "offline": False,
            "latency": 50,
            "downloadThroughput": 25 * 1024 * 1024 / 8,
            "uploadThroughput": 5 * 1024 * 1024 / 8,
            "connectionType": "wifi",
        },
    )
    started_at = time.perf_counter()
    page.goto(static_site_url, wait_until="load")
    page.get_by_label("Your dog's photo").wait_for(state="visible")
    elapsed_seconds = time.perf_counter() - started_at
    assert elapsed_seconds <= 5.0
