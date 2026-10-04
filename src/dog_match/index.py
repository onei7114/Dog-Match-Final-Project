"""Versioned, rebuildable manifest and embedding-matrix storage."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageOps

from dog_match.dataset import BreedPhoto, scan_dataset

INDEX_FORMAT_VERSION = 1
MANIFEST_NAME = "manifest.json"
EMBEDDINGS_NAME = "embeddings.npy"


class IndexUnavailableError(RuntimeError):
    """Raised when the reference index is missing, stale, or incompatible."""


@dataclass(frozen=True, slots=True)
class IndexManifest:
    format_version: int
    model_id: str
    model_revision: str
    preprocessing_version: str
    image_count: int
    embedding_dimension: int
    embeddings_sha256: str
    images: tuple[BreedPhoto, ...]
    source_inventory: tuple[tuple[str, int, int], ...] = ()


@dataclass(frozen=True, slots=True)
class ReferenceIndex:
    manifest: IndexManifest
    embeddings: NDArray[np.float32]

    @property
    def image_count(self) -> int:
        return len(self.manifest.images)

    @property
    def breed_count(self) -> int:
        return len({image.breed_name for image in self.manifest.images})


class ImageEncoder(Protocol):
    """Small interface required by the index builder."""

    model_id: str
    model_revision: str

    def encode(self, images: Sequence[Image.Image]) -> NDArray[np.float32]: ...


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False
        ) as file:
            temporary_path = Path(file.name)
            json.dump(payload, file, ensure_ascii=False, separators=(",", ":"))
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _inventory(dataset_root: Path) -> tuple[tuple[str, int, int], ...]:
    root = dataset_root.resolve(strict=True)
    inventory: list[tuple[str, int, int]] = []
    for path in root.rglob("*"):
        if path.suffix.casefold() not in {".jpg", ".jpeg"} or not path.is_file() or path.is_symlink():
            continue
        try:
            path.resolve(strict=True).relative_to(root)
            stat = path.stat()
        except (OSError, ValueError) as exc:
            raise IndexUnavailableError("Dataset inventory contains an inaccessible image") from exc
        inventory.append((path.relative_to(root).as_posix(), stat.st_size, stat.st_mtime_ns))
    return tuple(sorted(inventory))


def save_index(
    cache_dir: Path,
    images: tuple[BreedPhoto, ...],
    embeddings: NDArray[np.floating[Any]],
    model_id: str,
    model_revision: str,
    preprocessing_version: str,
    source_inventory: tuple[tuple[str, int, int], ...] | None = None,
) -> IndexManifest:
    """Atomically replace the embedding file and manifest after a full build."""
    vectors = np.asarray(embeddings, dtype=np.float32)
    if vectors.ndim != 2 or vectors.shape[0] != len(images) or vectors.shape[1] == 0:
        raise ValueError("Embedding matrix must have one non-empty vector per image")
    if not np.isfinite(vectors).all():
        raise ValueError("Embedding matrix contains non-finite values")
    norms = np.linalg.norm(vectors, axis=1)
    if not np.allclose(norms, 1.0, rtol=1e-4, atol=1e-4):
        raise ValueError("All image embeddings must be normalized to unit length")

    cache_dir.mkdir(parents=True, exist_ok=True)
    embeddings_path = cache_dir / EMBEDDINGS_NAME
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=cache_dir, suffix=".npy.tmp", delete=False) as file:
            temporary_path = Path(file.name)
            np.save(file, vectors, allow_pickle=False)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary_path, embeddings_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    manifest = IndexManifest(
        format_version=INDEX_FORMAT_VERSION,
        model_id=model_id,
        model_revision=model_revision,
        preprocessing_version=preprocessing_version,
        image_count=len(images),
        embedding_dimension=int(vectors.shape[1]),
        embeddings_sha256=_sha256(embeddings_path),
        images=images,
        source_inventory=(
            source_inventory
            if source_inventory is not None
            else tuple((image.relative_path, image.file_size, image.modified_ns) for image in images)
        ),
    )
    _atomic_write_json(cache_dir / MANIFEST_NAME, asdict(manifest))
    return manifest


def build_index(
    dataset_root: Path,
    cache_dir: Path,
    encoder: ImageEncoder,
    batch_size: int = 16,
    preprocessing_version: str = "clip-rgb-exif-v1",
) -> IndexManifest:
    """Validate and encode the read-only dataset, then publish one complete index."""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")
    scan = scan_dataset(dataset_root)
    if not scan.images:
        raise ValueError("No readable JPG/JPEG reference images were found")

    vectors: list[NDArray[np.float32]] = []
    root = dataset_root.resolve(strict=True)
    for offset in range(0, len(scan.images), batch_size):
        image_batch: list[Image.Image] = []
        try:
            for record in scan.images[offset : offset + batch_size]:
                image_path = root / record.relative_path
                with Image.open(image_path) as image:
                    image.load()
                    oriented = ImageOps.exif_transpose(image)
                    image_batch.append((oriented if oriented is not None else image).convert("RGB"))
            encoded = encoder.encode(image_batch)
            if encoded.shape[0] != len(image_batch):
                raise ValueError("Encoder returned a different number of vectors than input images")
            vectors.append(encoded)
        finally:
            for image in image_batch:
                image.close()

    matrix = np.concatenate(vectors, axis=0)
    return save_index(
        cache_dir=cache_dir,
        images=scan.images,
        embeddings=matrix,
        model_id=encoder.model_id,
        model_revision=encoder.model_revision,
        preprocessing_version=preprocessing_version,
        source_inventory=scan.inventory,
    )


def _read_manifest(path: Path) -> IndexManifest:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        images = tuple(BreedPhoto(**image) for image in payload.pop("images"))
        raw_inventory = payload.pop("source_inventory", None)
        if raw_inventory is not None:
            payload["source_inventory"] = tuple(
                (str(entry[0]), int(entry[1]), int(entry[2])) for entry in raw_inventory
            )
        manifest = IndexManifest(images=images, **payload)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise IndexUnavailableError("Index manifest is missing or invalid; rebuild the index") from exc
    if manifest.format_version != INDEX_FORMAT_VERSION or manifest.image_count != len(manifest.images):
        raise IndexUnavailableError("Index manifest version or image count is invalid; rebuild the index")
    return manifest


def load_index(
    cache_dir: Path,
    dataset_root: Path,
    model_id: str,
    model_revision: str,
    preprocessing_version: str,
) -> ReferenceIndex:
    """Load only a checksum-valid index matching the local image inventory."""
    manifest_path = cache_dir / MANIFEST_NAME
    embeddings_path = cache_dir / EMBEDDINGS_NAME
    if not manifest_path.is_file() or not embeddings_path.is_file():
        raise IndexUnavailableError("Reference index is missing; run `dog-match build-index`")

    manifest = _read_manifest(manifest_path)
    if (
        manifest.model_id != model_id
        or manifest.model_revision != model_revision
        or manifest.preprocessing_version != preprocessing_version
    ):
        raise IndexUnavailableError("Reference index uses a different model or preprocessing; rebuild it")
    if _sha256(embeddings_path) != manifest.embeddings_sha256:
        raise IndexUnavailableError("Reference index checksum failed; rebuild it")

    root = dataset_root.resolve(strict=True)
    for image in manifest.images:
        image_path = (root / image.relative_path).resolve(strict=True)
        try:
            image_path.relative_to(root)
        except ValueError as exc:
            raise IndexUnavailableError("Reference index contains a path outside the dataset") from exc
        stat = image_path.stat()
        if stat.st_size != image.file_size or stat.st_mtime_ns != image.modified_ns:
            raise IndexUnavailableError("Dataset image inventory changed; rebuild the reference index")
    if manifest.source_inventory and _inventory(root) != manifest.source_inventory:
        raise IndexUnavailableError("Dataset image inventory changed; rebuild the reference index")

    try:
        vectors = np.load(embeddings_path, mmap_mode="r", allow_pickle=False)
    except (OSError, ValueError) as exc:
        raise IndexUnavailableError("Reference vectors are unreadable; rebuild the index") from exc
    if vectors.shape != (manifest.image_count, manifest.embedding_dimension):
        raise IndexUnavailableError("Reference vector shape is invalid; rebuild the index")
    if not np.isfinite(vectors).all():
        raise IndexUnavailableError("Reference vectors contain invalid values; rebuild the index")
    return ReferenceIndex(manifest=manifest, embeddings=vectors)
