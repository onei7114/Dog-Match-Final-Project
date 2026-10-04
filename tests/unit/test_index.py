from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from dog_match.dataset import scan_dataset
from dog_match.index import IndexUnavailableError, build_index, load_index, save_index


class FixedEncoder:
    model_id = "test-model"
    model_revision = "test-revision"

    def encode(self, images: list[Image.Image]) -> np.ndarray:
        return np.tile(np.array([[1.0, 0.0]], dtype=np.float32), (len(images), 1))


def create_reference(root: Path, name: str = "dog.jpg") -> None:
    image_path = root / "collie dog" / name
    image_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), (25, 110, 40)).save(image_path, format="JPEG")


def test_build_and_load_index_preserves_manifest_and_vectors(tmp_path: Path) -> None:
    dataset_root = tmp_path / "dataset"
    cache_dir = tmp_path / "cache"
    create_reference(dataset_root)

    manifest = build_index(dataset_root, cache_dir, FixedEncoder(), batch_size=1)
    index = load_index(cache_dir, dataset_root, "test-model", "test-revision", "clip-rgb-exif-v1")

    assert manifest.image_count == 1
    assert index.breed_count == 1
    assert index.manifest.images[0].breed_name == "collie dog"
    assert np.allclose(index.embeddings, [[1.0, 0.0]])


def test_load_rejects_new_dataset_image_as_stale(tmp_path: Path) -> None:
    dataset_root = tmp_path / "dataset"
    cache_dir = tmp_path / "cache"
    create_reference(dataset_root)
    scan = scan_dataset(dataset_root)
    save_index(
        cache_dir,
        scan.images,
        np.array([[1.0, 0.0]], dtype=np.float32),
        "test-model",
        "test-revision",
        "clip-rgb-exif-v1",
    )
    create_reference(dataset_root, "new.jpg")

    with pytest.raises(IndexUnavailableError, match="inventory changed"):
        load_index(cache_dir, dataset_root, "test-model", "test-revision", "clip-rgb-exif-v1")


def test_unreadable_jpeg_is_recorded_but_does_not_break_index_startup(tmp_path: Path) -> None:
    dataset_root = tmp_path / "dataset"
    cache_dir = tmp_path / "cache"
    create_reference(dataset_root)
    broken_path = dataset_root / "collie dog" / "broken.jpg"
    broken_path.write_bytes(b"not a jpeg")

    scan = scan_dataset(dataset_root)
    manifest = build_index(dataset_root, cache_dir, FixedEncoder(), batch_size=2)
    index = load_index(cache_dir, dataset_root, "test-model", "test-revision", "clip-rgb-exif-v1")

    assert scan.image_count == 1
    assert len(scan.inventory) == 2
    assert manifest.image_count == 1
    assert len(manifest.source_inventory) == 2
    assert index.image_count == 1


def test_save_rejects_vectors_that_are_not_normalized(tmp_path: Path) -> None:
    dataset_root = tmp_path / "dataset"
    create_reference(dataset_root)
    image = scan_dataset(dataset_root).images[0]

    with pytest.raises(ValueError, match="normalized"):
        save_index(
            tmp_path / "cache",
            (image,),
            np.array([[2.0, 0.0]], dtype=np.float32),
            "test-model",
            "test-revision",
            "clip-rgb-exif-v1",
        )
