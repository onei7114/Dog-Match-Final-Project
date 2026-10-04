"""Typed application settings for local dataset and cache paths."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MODEL_ID = "openai/clip-vit-base-patch32"
DEFAULT_MODEL_REVISION = "3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000


@dataclass(frozen=True, slots=True)
class Settings:
    dataset_root: Path = Path("Dog-Breeds-Dataset")
    cache_dir: Path = Path(".cache/dog-match")
    max_upload_bytes: int = MAX_UPLOAD_BYTES
    max_image_pixels: int = MAX_IMAGE_PIXELS
    model_id: str = DEFAULT_MODEL_ID
    model_revision: str = DEFAULT_MODEL_REVISION
    host: str = "127.0.0.1"
    port: int = 8000

    def __post_init__(self) -> None:
        if self.max_upload_bytes <= 0:
            raise ValueError("max_upload_bytes must be greater than zero")
        if self.max_image_pixels <= 0:
            raise ValueError("max_image_pixels must be greater than zero")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")

    @classmethod
    def from_environment(cls) -> Settings:
        """Create settings from documented local environment overrides."""
        return cls(
            dataset_root=Path(os.getenv("DOG_MATCH_DATASET", "Dog-Breeds-Dataset")),
            cache_dir=Path(os.getenv("DOG_MATCH_CACHE", ".cache/dog-match")),
            max_upload_bytes=int(os.getenv("DOG_MATCH_MAX_UPLOAD_BYTES", MAX_UPLOAD_BYTES)),
            max_image_pixels=int(os.getenv("DOG_MATCH_MAX_IMAGE_PIXELS", MAX_IMAGE_PIXELS)),
            model_id=os.getenv("DOG_MATCH_MODEL_ID", DEFAULT_MODEL_ID),
            model_revision=os.getenv("DOG_MATCH_MODEL_REVISION", DEFAULT_MODEL_REVISION),
            host=os.getenv("DOG_MATCH_HOST", "127.0.0.1"),
            port=int(os.getenv("DOG_MATCH_PORT", "8000")),
        )
