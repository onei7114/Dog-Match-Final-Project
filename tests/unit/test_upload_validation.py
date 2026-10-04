from __future__ import annotations

import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from fastapi import Request
from PIL import Image

from dog_match.upload_validation import (
    MissingUploadError,
    UploadTooLargeError,
    UploadValidationError,
    read_validated_jpeg,
)


def run_async(awaitable: Any) -> Any:
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, awaitable).result()


def jpeg_bytes(size: tuple[int, int] = (12, 12)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, (30, 120, 50)).save(buffer, format="JPEG")
    return buffer.getvalue()


def multipart_request(file_bytes: bytes | None, *, field: str = "file", filename: str = "dog.jpg") -> Request:
    boundary = b"dog-match-test-boundary"
    if file_bytes is None:
        body = b"--" + boundary + b"--\r\n"
    else:
        body = (
            b"--" + boundary + b"\r\n"
            + f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode()
            + b"Content-Type: image/jpeg\r\n\r\n"
            + file_bytes
            + b"\r\n--"
            + boundary
            + b"--\r\n"
        )
    consumed = False

    async def receive() -> dict[str, Any]:
        nonlocal consumed
        if consumed:
            return {"type": "http.request", "body": b"", "more_body": False}
        consumed = True
        return {"type": "http.request", "body": body, "more_body": False}

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/v1/matches",
        "raw_path": b"/api/v1/matches",
        "query_string": b"",
        "headers": [
            (b"content-type", b"multipart/form-data; boundary=" + boundary),
            (b"content-length", str(len(body)).encode()),
        ],
        "server": ("testserver", 80),
        "client": ("testclient", 123),
    }
    return Request(scope, receive)


def test_reads_valid_jpeg_in_memory_and_returns_rgb_image() -> None:
    image = run_async(read_validated_jpeg(multipart_request(jpeg_bytes())))
    try:
        assert image.format == "JPEG" or image.mode == "RGB"
        assert image.mode == "RGB"
        assert image.size == (12, 12)
    finally:
        image.close()


def test_missing_file_field_has_distinct_error() -> None:
    with pytest.raises(MissingUploadError):
        run_async(read_validated_jpeg(multipart_request(None)))


def test_invalid_jpeg_content_is_rejected_even_with_jpg_filename() -> None:
    with pytest.raises(UploadValidationError, match="readable JPG"):
        run_async(read_validated_jpeg(multipart_request(b"not a jpeg")))


def test_upload_byte_limit_is_enforced_while_parsing() -> None:
    with pytest.raises(UploadTooLargeError):
        run_async(read_validated_jpeg(multipart_request(jpeg_bytes()), max_upload_bytes=16))


def test_oversized_content_length_maps_to_upload_too_large() -> None:
    request = multipart_request(jpeg_bytes())
    oversized_length = str(16 + 64 * 1024 + 1).encode()
    request.scope["headers"] = [
        (name, oversized_length if name == b"content-length" else value)
        for name, value in request.scope["headers"]
    ]

    with pytest.raises(UploadTooLargeError):
        run_async(read_validated_jpeg(request, max_upload_bytes=16))


def test_decoded_pixel_limit_is_enforced_before_image_processing() -> None:
    with pytest.raises(UploadValidationError, match="dimensions"):
        run_async(read_validated_jpeg(multipart_request(jpeg_bytes((20, 20))), max_image_pixels=100))


def test_upload_parsing_never_creates_a_temporary_file(monkeypatch: pytest.MonkeyPatch) -> None:
    def reject_temp_file(*args: object, **kwargs: object) -> None:
        raise AssertionError("upload parser attempted to create a temporary file")

    monkeypatch.setattr(tempfile, "NamedTemporaryFile", reject_temp_file)
    image = run_async(read_validated_jpeg(multipart_request(jpeg_bytes())))
    image.close()
