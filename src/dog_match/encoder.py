"""Pinned local CLIP image encoder used for reference and upload photos."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageOps

from dog_match.config import DEFAULT_MODEL_ID, DEFAULT_MODEL_REVISION

PREPROCESSING_VERSION = "clip-rgb-exif-v1"


class ClipImageEncoder:
    """Encode images into normalized CLIP feature vectors on the selected device."""

    def __init__(
        self,
        model: Any,
        processor: Any,
        device: Any,
        model_id: str,
        model_revision: str,
    ) -> None:
        self.model = model.to(device).eval()
        self.processor = processor
        self.device = device
        self.model_id = model_id
        self.model_revision = model_revision

    @classmethod
    def from_pretrained(
        cls,
        model_id: str = DEFAULT_MODEL_ID,
        revision: str = DEFAULT_MODEL_REVISION,
        local_files_only: bool = False,
    ) -> ClipImageEncoder:
        """Load only the explicitly pinned model revision."""
        import torch
        from transformers import CLIPModel, CLIPProcessor

        processor = CLIPProcessor.from_pretrained(
            model_id,
            revision=revision,
            local_files_only=local_files_only,
        )
        model = CLIPModel.from_pretrained(
            model_id,
            revision=revision,
            local_files_only=local_files_only,
        )
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return cls(model, processor, device, model_id, revision)

    def encode(self, images: Sequence[Image.Image]) -> NDArray[np.float32]:
        """Return one unit-length float32 vector per RGB image."""
        import torch

        if not images:
            return np.empty((0, 0), dtype=np.float32)
        rgb_images: list[Image.Image] = []
        for image in images:
            oriented = ImageOps.exif_transpose(image)
            rgb_images.append((oriented if oriented is not None else image).convert("RGB"))
        inputs = self.processor(images=rgb_images, return_tensors="pt")
        pixel_values = inputs["pixel_values"].to(self.device)
        with torch.inference_mode():
            features = self.model.get_image_features(pixel_values=pixel_values)
            if not isinstance(features, torch.Tensor):
                raise RuntimeError("CLIP image encoder returned an unsupported feature value")
            features = torch.nn.functional.normalize(features, p=2, dim=1)
        vectors = features.detach().to(device="cpu", dtype=torch.float32).numpy()
        if not np.isfinite(vectors).all():
            raise RuntimeError("CLIP image encoder returned non-finite vectors")
        return np.asarray(vectors, dtype=np.float32)
