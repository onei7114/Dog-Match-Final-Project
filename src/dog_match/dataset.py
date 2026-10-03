"""Read-only dataset traversal and folder-derived breed labels."""

from __future__ import annotations

import hashlib
import warnings
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, UnidentifiedImageError


@dataclass(frozen=True, slots=True)
class BreedPhoto:
    """One readable reference image discovered below the dataset root."""

    reference_id: str
    relative_path: str
    breed_name: str
    file_size: int
    modified_ns: int


@dataclass(frozen=True, slots=True)
class DatasetIssue:
    """A dataset path that could not be used as a reference image."""

    relative_path: str
    reason: str


@dataclass(frozen=True, slots=True)
class DatasetScan:
    """Inventory produced by a read-only dataset scan."""

    breed_count: int
    images: tuple[BreedPhoto, ...]
    empty_breed_folders: tuple[str, ...]
    issues: tuple[DatasetIssue, ...]
    inventory: tuple[tuple[str, int, int], ...]

    @property
    def image_count(self) -> int:
        return len(self.images)


def _reference_id(relative_path: str) -> str:
    digest = hashlib.sha256(relative_path.encode("utf-8")).hexdigest()
    return digest[:16]


def _is_readable_jpeg(path: Path) -> bool:
    """Require a JPEG file that Pillow can verify and fully decode."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(path) as image:
            if image.format != "JPEG":
                return False
            image.verify()
        with Image.open(path) as image:
            image.load()
    return True


def scan_dataset(dataset_root: Path) -> DatasetScan:
    """Recursively list readable JPG/JPEG references without modifying files."""
    root = dataset_root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise NotADirectoryError(f"Dataset path is not a directory: {dataset_root}")

    breed_folders = sorted(
        (path for path in root.iterdir() if path.is_dir() and not path.is_symlink()),
        key=lambda path: path.name.casefold(),
    )
    candidates: list[Path] = []
    issues: list[DatasetIssue] = []
    empty_folders: list[str] = []

    for breed_folder in breed_folders:
        folder_images: list[Path] = []
        for path in breed_folder.rglob("*"):
            suffix = path.suffix.casefold()
            if suffix not in {".jpg", ".jpeg"} or not path.is_file():
                continue
            try:
                resolved = path.resolve(strict=True)
                resolved.relative_to(root)
            except (OSError, ValueError):
                issues.append(
                    DatasetIssue(path.relative_to(root).as_posix(), "path escapes dataset root or is unreadable")
                )
                continue
            if path.is_symlink():
                issues.append(DatasetIssue(path.relative_to(root).as_posix(), "symbolic links are not indexed"))
                continue
            folder_images.append(path)
        if folder_images:
            candidates.extend(folder_images)
        else:
            empty_folders.append(breed_folder.name)

    images: list[BreedPhoto] = []
    inventory: list[tuple[str, int, int]] = []
    for path in sorted(candidates, key=lambda item: item.relative_to(root).as_posix().casefold()):
        relative_path = path.relative_to(root).as_posix()
        try:
            stat = path.stat()
            inventory.append((relative_path, stat.st_size, stat.st_mtime_ns))
        except OSError as exc:
            issues.append(DatasetIssue(relative_path, f"file metadata cannot be read: {type(exc).__name__}"))
            continue
        try:
            if not _is_readable_jpeg(path):
                issues.append(DatasetIssue(relative_path, "file content is not JPEG"))
                continue
        except (OSError, SyntaxError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
            issues.append(DatasetIssue(relative_path, f"image cannot be decoded: {type(exc).__name__}"))
            continue
        images.append(
            BreedPhoto(
                reference_id=_reference_id(relative_path),
                relative_path=relative_path,
                breed_name=path.parent.name,
                file_size=stat.st_size,
                modified_ns=stat.st_mtime_ns,
            )
        )

    return DatasetScan(
        breed_count=len(breed_folders),
        images=tuple(images),
        empty_breed_folders=tuple(empty_folders),
        issues=tuple(issues),
        inventory=tuple(sorted(inventory)),
    )
