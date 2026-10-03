from __future__ import annotations

import numpy as np
import pytest

from dog_match.dataset import BreedPhoto
from dog_match.index import IndexManifest, ReferenceIndex
from scripts.evaluate_matching import exclude_evaluation_set, write_report


def make_index() -> ReferenceIndex:
    images = (
        BreedPhoto("eval-1", "breed a/one.jpg", "breed a", 1, 1),
        BreedPhoto("ref-a", "breed a/two.jpg", "breed a", 1, 1),
        BreedPhoto("eval-2", "breed b/one.jpg", "breed b", 1, 1),
        BreedPhoto("ref-b", "breed b/two.jpg", "breed b", 1, 1),
    )
    manifest = IndexManifest(1, "model", "revision", "preprocessing", 4, 2, "checksum", images)
    vectors = np.array([[1, 0], [0.9, 0.1], [0, 1], [0.1, 0.9]], dtype=np.float32)
    return ReferenceIndex(manifest, vectors)


def test_evaluation_photos_are_all_removed_from_reference_candidates() -> None:
    sample = {"eval-1", "eval-2"}

    reference_index = exclude_evaluation_set(make_index(), sample)

    assert {image.reference_id for image in reference_index.manifest.images} == {"ref-a", "ref-b"}
    assert reference_index.image_count == 2
    assert reference_index.embeddings.shape == (2, 2)


def test_evaluation_set_cannot_remove_every_reference() -> None:
    index = make_index()

    with pytest.raises(ValueError, match="No reference images remain"):
        exclude_evaluation_set(index, {image.reference_id for image in index.manifest.images})


def test_accuracy_report_records_model_and_agreement(tmp_path: Path) -> None:
    report_path = tmp_path / "accuracy-evaluation.md"

    write_report(
        report_path,
        correct=80,
        total=100,
        rows=[("beagle dog/test.jpg", "beagle dog", True)],
        seed=42,
        model_id="openai/clip-vit-base-patch32",
        model_revision="immutable-revision",
        strategy_correct={"nearest_photo": 80, "breed_centroid": 75},
    )

    report = report_path.read_text(encoding="utf-8")
    assert "80/100 (80.0%)" in report
    assert "`immutable-revision`" in report
    assert "PASS" in report
