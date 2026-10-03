"""Bounded, memory-only multipart JPEG parsing and image validation."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING

from fastapi import Request
from PIL import Image, ImageOps, UnidentifiedImageError
from python_multipart import MultipartParser
from python_multipart.exceptions import MultipartParseError
from python_multipart.multipart import parse_options_header

from dog_match.config import MAX_IMAGE_PIXELS, MAX_UPLOAD_BYTES

if TYPE_CHECKING:
    from python_multipart.multipart import MultipartCallbacks

MULTIPART_OVERHEAD_BYTES = 64 * 1024
MAX_HEADER_BYTES = 8192
MAX_HEADERS_PER_PART = 16


class UploadValidationError(ValueError):
    """The request does not contain one readable JPEG in the expected field."""


class MissingUploadError(UploadValidationError):
    """The multipart request did not include the required file field."""


class UploadTooLargeError(UploadValidationError):
    """The request or uploaded image exceeds its configured byte limit."""


@dataclass(slots=True)
class _MultipartState:
    image_bytes: bytearray
    part_count: int = 0
    completed_file_count: int = 0
    current_field_name: bytes | None = None
    current_is_file: bool = False
    header_name: bytearray | None = None
    header_value: bytearray | None = None
    headers: dict[bytes, bytes] | None = None
    header_bytes: int = 0
    header_count: int = 0


def _multipart_callbacks(state: _MultipartState, max_upload_bytes: int) -> MultipartCallbacks:
    def on_part_begin() -> None:
        state.part_count += 1
        if state.part_count > 1:
            raise UploadValidationError("Submit exactly one photo in the file field")
        state.headers = {}
        state.current_field_name = None
        state.current_is_file = False
        state.header_bytes = 0
        state.header_count = 0

    def on_header_begin() -> None:
        state.header_name = bytearray()
        state.header_value = bytearray()
        state.header_bytes = 0

    def on_header_field(data: bytes, start: int, end: int) -> None:
        state.header_bytes += end - start
        if state.header_bytes > MAX_HEADER_BYTES:
            raise UploadValidationError("Multipart header exceeds the supported limit")
        if state.header_name is not None:
            state.header_name.extend(data[start:end])

    def on_header_value(data: bytes, start: int, end: int) -> None:
        state.header_bytes += end - start
        if state.header_bytes > MAX_HEADER_BYTES:
            raise UploadValidationError("Multipart header exceeds the supported limit")
        if state.header_value is not None:
            state.header_value.extend(data[start:end])

    def on_header_end() -> None:
        if state.headers is None or state.header_name is None or state.header_value is None:
            raise UploadValidationError("Malformed multipart headers")
        state.header_count += 1
        if state.header_count > MAX_HEADERS_PER_PART:
            raise UploadValidationError("Multipart part has too many headers")
        state.headers[bytes(state.header_name).strip().lower()] = bytes(state.header_value).strip()

    def on_headers_finished() -> None:
        if state.headers is None:
            raise UploadValidationError("Malformed multipart headers")
        disposition_header = state.headers.get(b"content-disposition")
        if disposition_header is None:
            raise UploadValidationError("Missing file field")
        disposition, parameters = parse_options_header(disposition_header)
        field_name = parameters.get(b"name")
        filename = parameters.get(b"filename")
        if disposition != b"form-data":
            raise UploadValidationError("The uploaded form could not be read")
        if field_name != b"file" or filename is None:
            raise MissingUploadError("Choose a JPG or JPEG photo to upload")
        if filename == b"":
            raise UploadValidationError("Submit one photo using the file field")
        state.current_field_name = field_name
        state.current_is_file = True

    def on_part_data(data: bytes, start: int, end: int) -> None:
        if not state.current_is_file:
            raise UploadValidationError("Unexpected form field")
        if len(state.image_bytes) + end - start > max_upload_bytes:
            raise UploadTooLargeError("The uploaded photo exceeds the 10 MiB limit")
        state.image_bytes.extend(data[start:end])

    def on_part_end() -> None:
        if state.current_is_file:
            state.completed_file_count += 1
            state.current_is_file = False

    return {
        "on_part_begin": on_part_begin,
        "on_header_begin": on_header_begin,
        "on_header_field": on_header_field,
        "on_header_value": on_header_value,
        "on_header_end": on_header_end,
        "on_headers_finished": on_headers_finished,
        "on_part_data": on_part_data,
        "on_part_end": on_part_end,
    }


def _decode_jpeg(image_bytes: bytes, max_image_pixels: int) -> Image.Image:
    if not image_bytes.startswith(b"\xff\xd8"):
        raise UploadValidationError("Choose a readable JPG or JPEG photo and try again")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(image_bytes)) as image:
                if image.format != "JPEG":
                    raise UploadValidationError("Choose a readable JPG or JPEG photo and try again")
                width, height = image.size
                if width <= 0 or height <= 0 or width * height > max_image_pixels:
                    raise UploadValidationError("The photo dimensions exceed the supported limit")
                image.verify()
            with Image.open(BytesIO(image_bytes)) as image:
                image.load()
                oriented = ImageOps.exif_transpose(image)
                rgb_image = (oriented if oriented is not None else image).convert("RGB")
                rgb_image.load()
                return rgb_image
    except UploadValidationError:
        raise
    except (OSError, SyntaxError, ValueError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise UploadValidationError("Choose a readable JPG or JPEG photo and try again") from exc


async def read_validated_jpeg(
    request: Request,
    max_upload_bytes: int = MAX_UPLOAD_BYTES,
    max_image_pixels: int = MAX_IMAGE_PIXELS,
) -> Image.Image:
    """Parse one bounded multipart photo entirely in memory and return decoded RGB pixels."""
    content_type_header = request.headers.get("content-type", "")
    media_type, parameters = parse_options_header(content_type_header.encode("latin-1"))
    boundary = parameters.get(b"boundary")
    if media_type != b"multipart/form-data" or not boundary:
        raise UploadValidationError("Submit a JPG or JPEG photo using multipart form data")

    content_length = request.headers.get("content-length")
    maximum_request_bytes = max_upload_bytes + MULTIPART_OVERHEAD_BYTES
    if content_length is not None:
        try:
            declared_length = int(content_length)
        except ValueError as exc:
            raise UploadValidationError("Invalid request length") from exc
        if declared_length > maximum_request_bytes:
            raise UploadTooLargeError("The uploaded photo exceeds the configured byte limit")

    state = _MultipartState(image_bytes=bytearray())
    parser = MultipartParser(
        boundary,
        _multipart_callbacks(state, max_upload_bytes),
        max_size=maximum_request_bytes,
    )
    bytes_received = 0
    try:
        async for chunk in request.stream():
            bytes_received += len(chunk)
            if bytes_received > maximum_request_bytes:
                raise UploadTooLargeError("The uploaded photo exceeds the 10 MiB limit")
            parser.write(chunk)
        parser.finalize()
    except UploadValidationError:
        raise
    except MultipartParseError as exc:
        raise UploadValidationError("The uploaded form could not be read") from exc
    except (ValueError, TypeError) as exc:
        raise UploadValidationError("The uploaded form could not be read") from exc

    if state.part_count == 0 or state.completed_file_count == 0:
        raise MissingUploadError("Choose a JPG or JPEG photo to upload")
    return _decode_jpeg(bytes(state.image_bytes), max_image_pixels)
