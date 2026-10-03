from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import cast

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from dog_match.app import create_app
from dog_match.config import Settings
from dog_match.dataset import BreedPhoto
from dog_match.encoder import ClipImageEncoder
from dog_match.index import IndexManifest, ReferenceIndex


class FixedEncoder:
    model_id = "test-model"
    model_revision = "test-revision"

    def encode(self, images: list[Image.Image]) -> np.ndarray:
        return np.array([[1.0, 0.0]], dtype=np.float32)


def valid_jpeg() -> bytes:
    output = BytesIO()
    Image.new("RGB", (8, 8), (20, 90, 35)).save(output, format="JPEG")
    return output.getvalue()


def test_missing_file_returns_documented_error(tmp_path: Path) -> None:
    record = BreedPhoto("reference-id", "breed dog/ref.jpg", "breed dog", 1, 1)
    manifest = IndexManifest(1, "test", "test", "test", 1, 2, "x", (record,))
    index = ReferenceIndex(manifest, np.array([[1.0, 0.0]], dtype=np.float32))
    settings = Settings(dataset_root=tmp_path, cache_dir=tmp_path / "cache")
    client = TestClient(create_app(settings, index, cast(ClipImageEncoder, FixedEncoder())))

    response = client.post("/api/v1/matches", files={"other": ("dog.jpg", b"bad", "image/jpeg")})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "missing_file"
    assert "stack" not in response.text.lower()


def make_client(tmp_path: Path, *, max_upload_bytes: int = 10 * 1024 * 1024) -> TestClient:
    record = BreedPhoto("reference-id", "breed dog/ref.jpg", "breed dog", 1, 1)
    manifest = IndexManifest(1, "test", "test", "test", 1, 2, "x", (record,))
    index = ReferenceIndex(manifest, np.array([[1.0, 0.0]], dtype=np.float32))
    settings = Settings(
        dataset_root=tmp_path,
        cache_dir=tmp_path / "cache",
        max_upload_bytes=max_upload_bytes,
    )
    return TestClient(create_app(settings, index, cast(ClipImageEncoder, FixedEncoder())))


def test_invalid_jpeg_returns_safe_error_without_partial_match(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/api/v1/matches",
        files={"file": ("dog.jpg", b"not-a-jpeg", "image/jpeg")},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "invalid_jpeg"
    assert "breed_name" not in response.json()


def test_oversized_upload_maps_to_413(tmp_path: Path) -> None:
    client = make_client(tmp_path, max_upload_bytes=16)

    response = client.post(
        "/api/v1/matches",
        files={"file": ("dog.jpg", b"a" * 100, "image/jpeg")},
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "upload_too_large"


def test_unexpected_matcher_failure_returns_safe_500(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = make_client(tmp_path)

    def fail_match(*args: object, **kwargs: object) -> None:
        raise RuntimeError("private diagnostic detail")

    monkeypatch.setattr("dog_match.app.find_closest_reference", fail_match)
    response = client.post(
        "/api/v1/matches",
        files={"file": ("dog.jpg", valid_jpeg(), "image/jpeg")},
    )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "match_failed"
    assert "private diagnostic detail" not in response.text


def test_unavailable_index_returns_503_without_fabricating_result(tmp_path: Path) -> None:
    settings = Settings(dataset_root=tmp_path, cache_dir=tmp_path / "cache")
    client = TestClient(create_app(settings))

    response = client.post(
        "/api/v1/matches",
        files={"file": ("dog.jpg", b"valid-looking-placeholder", "image/jpeg")},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "index_unavailable"
    assert "breed_name" not in response.json()
