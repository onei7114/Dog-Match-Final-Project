from __future__ import annotations

import numpy as np
import pytest

from dog_match.dataset import BreedPhoto
from dog_match.index import IndexManifest, ReferenceIndex
from dog_match.matcher import cosine_to_percent, find_closest_reference


def make_index() -> ReferenceIndex:
    images = (
        BreedPhoto("id-b", "terrier dog/b.jpg", "terrier dog", 1, 1),
        BreedPhoto("id-a", "collie dog/a.jpg", "collie dog", 1, 1),
    )
    manifest = IndexManifest(
        format_version=1,
        model_id="test-model",
        model_revision="test-revision",
        preprocessing_version="test-preprocessor",
        image_count=2,
        embedding_dimension=2,
        embeddings_sha256="test",
        images=images,
    )
    vectors = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float32)
    return ReferenceIndex(manifest, vectors)


def test_score_conversion_clamps_to_one_through_one_hundred() -> None:
    assert cosine_to_percent(-1.0) == 1
    assert cosine_to_percent(1.0) == 100
    assert 1 <= cosine_to_percent(0.0) <= 100
    with pytest.raises(ValueError):
        cosine_to_percent(float("nan"))


def test_matcher_returns_highest_unrounded_cosine_match() -> None:
    result = find_closest_reference(make_index(), np.array([0.99, 0.01], dtype=np.float32))

    assert result.reference_id == "id-a"
    assert result.breed_name == "collie dog"
    assert result.similarity_percent == 100


def test_matcher_breaks_exact_ties_by_relative_path() -> None:
    index = make_index()
    index.embeddings[:] = np.array([[1.0, 0.0], [1.0, 0.0]], dtype=np.float32)

    result = find_closest_reference(index, np.array([1.0, 0.0], dtype=np.float32))

    assert result.reference_id == "id-a"
    assert result.breed_name == "collie dog"


def test_matcher_can_exclude_the_evaluation_photo() -> None:
    result = find_closest_reference(
        make_index(),
        np.array([1.0, 0.0], dtype=np.float32),
        exclude_reference_id="id-a",
    )

    assert result.reference_id == "id-b"
