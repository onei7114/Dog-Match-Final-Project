from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import cast

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from dog_match.app import create_app
from dog_match.config import Settings
from dog_match.dataset import scan_dataset
from dog_match.encoder import ClipImageEncoder
from dog_match.index import IndexManifest, ReferenceIndex


class FixedEncoder:
    model_id = "test-model"
    model_revision = "test-revision"

    def encode(self, images: list[Image.Image]) -> np.ndarray:
        return np.tile(np.array([[1.0, 0.0]], dtype=np.float32), (len(images), 1))


def jpeg_bytes(color: tuple[int, int, int] = (20, 120, 40)) -> bytes:
    output = BytesIO()
    Image.new("RGB", (16, 16), color).save(output, format="JPEG")
    return output.getvalue()


def make_client(tmp_path: Path) -> tuple[TestClient, bytes]:
    dataset_root = tmp_path / "Dog-Breeds-Dataset"
    reference_path = dataset_root / "border collie dog" / "ref.jpg"
    reference_path.parent.mkdir(parents=True)
    reference_path.write_bytes(jpeg_bytes((10, 90, 30)))
    photo = scan_dataset(dataset_root).images[0]
    manifest = IndexManifest(
        format_version=1,
        model_id="test-model",
        model_revision="test-revision",
        preprocessing_version="clip-rgb-exif-v1",
        image_count=1,
        embedding_dimension=2,
        embeddings_sha256="test-only",
        images=(photo,),
    )
    index = ReferenceIndex(manifest, np.array([[1.0, 0.0]], dtype=np.float32))
    settings = Settings(dataset_root=dataset_root, cache_dir=tmp_path / "cache")
    app = create_app(settings, index, cast(ClipImageEncoder, FixedEncoder()))
    return TestClient(app), reference_path.read_bytes()


def test_match_endpoint_returns_folder_label_and_reference_photo(tmp_path: Path) -> None:
    client, reference_bytes = make_client(tmp_path)

    response = client.post(
        "/api/v1/matches",
        files={"file": ("user-photo.jpg", jpeg_bytes(), "image/jpeg")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["breed_name"] == "border collie dog"
    assert 1 <= body["similarity_percent"] <= 100
    assert body["reference_image_url"].startswith("/api/v1/reference-images/")
    assert "not a guaranteed breed identification" in body["disclaimer"]
    image_response = client.get(body["reference_image_url"])
    assert image_response.status_code == 200
    assert image_response.headers["content-type"] == "image/jpeg"
    assert image_response.content == reference_bytes
    assert not (tmp_path / "user-photo.jpg").exists()


def test_unknown_reference_id_does_not_map_to_a_filesystem_path(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)

    response = client.get("/api/v1/reference-images/../../outside.jpg")

    assert response.status_code in {404, 422}


def test_deleted_reference_photo_returns_safe_unavailable_response(tmp_path: Path) -> None:
    client, _ = make_client(tmp_path)
    reference_path = tmp_path / "Dog-Breeds-Dataset" / "border collie dog" / "ref.jpg"
    reference_path.unlink()

    response = client.get("/api/v1/reference-images/" + client.app.state.search_index.manifest.images[0].reference_id)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "index_unavailable"
    assert str(reference_path) not in response.text


def test_health_is_ready_only_when_index_is_loaded(tmp_path: Path) -> None:
    settings = Settings(dataset_root=tmp_path / "missing", cache_dir=tmp_path / "cache")
    client = TestClient(create_app(settings))

    response = client.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "index_unavailable"


def test_static_page_and_assets_are_served_same_origin(tmp_path: Path) -> None:
    settings = Settings(dataset_root=tmp_path / "missing", cache_dir=tmp_path / "cache")
    client = TestClient(create_app(settings))

    page = client.get("/")
    stylesheet = client.get("/static/styles.css")
    script = client.get("/static/app.js")

    assert page.status_code == 200
    assert "Who does your dog look like?" in page.text
    assert "Reference photos: Dog-Breeds-Dataset" in page.text
    assert stylesheet.status_code == 200
    assert script.status_code == 200
