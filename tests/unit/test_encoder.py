from __future__ import annotations

from typing import Any

import numpy as np
import pytest
import torch
from PIL import Image

from dog_match.encoder import ClipImageEncoder


class FakeProcessor:
    def __init__(self) -> None:
        self.seen_modes: list[str] = []

    def __call__(self, *, images: list[Image.Image], return_tensors: str) -> dict[str, torch.Tensor]:
        assert return_tensors == "pt"
        self.seen_modes = [image.mode for image in images]
        return {"pixel_values": torch.tensor([[3.0, 4.0] for _ in images])}


class FakeModel:
    def to(self, device: torch.device) -> FakeModel:
        return self

    def eval(self) -> FakeModel:
        return self

    def get_image_features(self, *, pixel_values: torch.Tensor) -> torch.Tensor:
        return pixel_values


def test_encoder_converts_images_to_rgb_and_normalizes_vectors() -> None:
    processor = FakeProcessor()
    encoder = ClipImageEncoder(
        model=FakeModel(),
        processor=processor,
        device=torch.device("cpu"),
        model_id="test-model",
        model_revision="test-revision",
    )
    image = Image.new("L", (8, 8), 128)

    vectors = encoder.encode([image])

    assert processor.seen_modes == ["RGB"]
    assert vectors.dtype == np.float32
    assert np.allclose(vectors, [[0.6, 0.8]])
    assert np.isclose(np.linalg.norm(vectors[0]), 1.0)
    image.close()


def test_encoder_returns_empty_matrix_for_empty_batch() -> None:
    encoder = ClipImageEncoder(
        model=FakeModel(),
        processor=FakeProcessor(),
        device=torch.device("cpu"),
        model_id="test-model",
        model_revision="test-revision",
    )

    vectors = encoder.encode([])

    assert vectors.shape == (0, 0)


class InvalidFeatureModel(FakeModel):
    def get_image_features(self, *, pixel_values: torch.Tensor) -> Any:
        return torch.tensor([[float("nan"), 0.0]])


def test_encoder_rejects_non_finite_features() -> None:
    encoder = ClipImageEncoder(
        model=InvalidFeatureModel(),
        processor=FakeProcessor(),
        device=torch.device("cpu"),
        model_id="test-model",
        model_revision="test-revision",
    )
    image = Image.new("RGB", (8, 8))
    try:
        with pytest.raises(RuntimeError, match="non-finite"):
            encoder.encode([image])
    finally:
        image.close()
