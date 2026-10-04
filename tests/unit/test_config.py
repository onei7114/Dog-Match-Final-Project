from __future__ import annotations

from pathlib import Path

import pytest

from dog_match.config import DEFAULT_MODEL_REVISION, MAX_IMAGE_PIXELS, MAX_UPLOAD_BYTES, Settings


def test_settings_use_documented_local_defaults() -> None:
    settings = Settings()

    assert settings.dataset_root == Path("Dog-Breeds-Dataset")
    assert settings.cache_dir == Path(".cache/dog-match")
    assert settings.max_upload_bytes == MAX_UPLOAD_BYTES
    assert settings.max_image_pixels == MAX_IMAGE_PIXELS
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.model_revision == DEFAULT_MODEL_REVISION


def test_settings_read_path_and_limits_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOG_MATCH_DATASET", "D:/data/dogs")
    monkeypatch.setenv("DOG_MATCH_CACHE", "D:/cache/dog-match")
    monkeypatch.setenv("DOG_MATCH_MAX_UPLOAD_BYTES", "4096")
    monkeypatch.setenv("DOG_MATCH_PORT", "8123")

    settings = Settings.from_environment()

    assert settings.dataset_root == Path("D:/data/dogs")
    assert settings.cache_dir == Path("D:/cache/dog-match")
    assert settings.max_upload_bytes == 4096
    assert settings.port == 8123


@pytest.mark.parametrize(
    "overrides",
    [
        {"max_upload_bytes": 0},
        {"max_image_pixels": -1},
        {"port": 70000},
    ],
)
def test_settings_reject_invalid_limits(overrides: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        Settings(**overrides)
