from __future__ import annotations

from pathlib import Path

from PIL import Image

from dog_match.dataset import scan_dataset


def write_jpeg(path: Path, color: tuple[int, int, int] = (30, 120, 50)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (12, 12), color).save(path, format="JPEG")


def test_scan_uses_immediate_parent_folder_title_and_stable_order(tmp_path: Path) -> None:
    root = tmp_path / "Dog-Breeds-Dataset"
    write_jpeg(root / "collie dog" / "b.jpg")
    write_jpeg(root / "collie dog" / "a.JPG")
    write_jpeg(root / "terrier dog" / "c.jpeg", (150, 20, 20))

    first = scan_dataset(root)
    second = scan_dataset(root)

    assert first.breed_count == 2
    assert first.image_count == 3
    assert [image.relative_path for image in first.images] == [
        "collie dog/a.JPG",
        "collie dog/b.jpg",
        "terrier dog/c.jpeg",
    ]
    assert {image.breed_name for image in first.images} == {"collie dog", "terrier dog"}
    assert [image.reference_id for image in first.images] == [image.reference_id for image in second.images]


def test_scan_reports_empty_folders_and_ignores_non_jpeg_files(tmp_path: Path) -> None:
    root = tmp_path / "dataset"
    (root / "empty breed").mkdir(parents=True)
    write_jpeg(root / "beagle dog" / "good.jpg")
    (root / "beagle dog" / "notes.txt").write_text("not an image", encoding="utf-8")

    scan = scan_dataset(root)

    assert scan.breed_count == 2
    assert scan.image_count == 1
    assert scan.empty_breed_folders == ("empty breed",)
    assert scan.issues == ()


def test_scan_reports_jpeg_extension_with_invalid_content(tmp_path: Path) -> None:
    root = tmp_path / "dataset"
    invalid_path = root / "pug dog" / "broken.jpg"
    invalid_path.parent.mkdir(parents=True)
    invalid_path.write_bytes(b"not a jpeg")

    scan = scan_dataset(root)

    assert scan.image_count == 0
    assert scan.issues[0].relative_path == "pug dog/broken.jpg"
    assert scan.inventory[0][0] == "pug dog/broken.jpg"
