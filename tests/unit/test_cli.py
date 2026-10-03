from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import dog_match.cli as cli
import numpy as np
import pytest
from PIL import Image

from dog_match.cli import build_parser, main
from dog_match.dataset import BreedPhoto
from dog_match.index import IndexManifest, IndexUnavailableError, ReferenceIndex


def write_jpeg(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), (20, 80, 40)).save(path, format="JPEG")


def test_parser_exposes_required_operator_commands() -> None:
    parser = build_parser()

    args = parser.parse_args(["validate-dataset", "--dataset", "./Dog-Breeds-Dataset"])

    assert args.command == "validate-dataset"
    assert args.dataset == "./Dog-Breeds-Dataset"
    assert callable(args.handler)


def test_validate_dataset_command_reports_counts_and_folder_names(tmp_path: Path, capsys: object) -> None:
    dataset = tmp_path / "dataset"
    write_jpeg(dataset / "beagle dog" / "one.jpg")

    exit_code = main(["validate-dataset", "--dataset", str(dataset)])
    output = capsys.readouterr().out
    report = json.loads(output)

    assert exit_code == 0
    assert report["breed_folder_count"] == 1
    assert report["readable_jpeg_count"] == 1
    assert report["issues"] == []


def test_validate_dataset_returns_failure_when_no_readable_photos_exist(tmp_path: Path, capsys: object) -> None:
    dataset = tmp_path / "dataset"
    dataset.mkdir()

    exit_code = main(["validate-dataset", "--dataset", str(dataset)])
    report = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert report["readable_jpeg_count"] == 0


def test_build_index_command_uses_local_dataset_and_cache_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: Any,
) -> None:
    dataset = tmp_path / "dataset"
    cache = tmp_path / "cache"
    fake_encoder = object()
    manifest = IndexManifest(1, "test-model", "revision", "preprocessing", 1, 2, "sum", ())
    monkeypatch.setattr(cli.ClipImageEncoder, "from_pretrained", staticmethod(lambda **kwargs: fake_encoder))
    called: dict[str, object] = {}

    def fake_build_index(**kwargs: object) -> IndexManifest:
        called.update(kwargs)
        return manifest

    monkeypatch.setattr(cli, "build_index", fake_build_index)

    exit_code = main(["build-index", "--dataset", str(dataset), "--cache-dir", str(cache), "--batch-size", "4"])
    report = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert called["dataset_root"] == dataset
    assert called["cache_dir"] == cache
    assert called["encoder"] is fake_encoder
    assert called["batch_size"] == 4
    assert report["reference_image_count"] == 1


def test_serve_command_loads_index_and_starts_loopback_server(monkeypatch: pytest.MonkeyPatch) -> None:
    record = BreedPhoto("id", "breed dog/ref.jpg", "breed dog", 1, 1)
    manifest = IndexManifest(1, "test-model", "revision", "preprocessing", 1, 2, "sum", (record,))
    index = ReferenceIndex(manifest, np.array([[1.0, 0.0]], dtype=np.float32))
    fake_encoder = object()
    monkeypatch.setattr(cli, "load_index", lambda *args: index)
    monkeypatch.setattr(cli.ClipImageEncoder, "from_pretrained", staticmethod(lambda **kwargs: fake_encoder))
    server_args: dict[str, object] = {}

    def fake_run(app: object, **kwargs: object) -> None:
        server_args.update(kwargs)
        assert app.state.search_index is index
        assert app.state.image_encoder is fake_encoder

    monkeypatch.setattr(cli.uvicorn, "run", fake_run)

    exit_code = main(["serve"])

    assert exit_code == 0
    assert server_args["host"] == "127.0.0.1"
    assert server_args["port"] == 8000


def test_serve_reports_missing_index_without_starting_server(
    monkeypatch: pytest.MonkeyPatch,
    capsys: Any,
) -> None:
    monkeypatch.setattr(cli, "load_index", lambda *args: (_ for _ in ()).throw(IndexUnavailableError("index missing")))

    exit_code = main(["serve"])
    error = capsys.readouterr().err

    assert exit_code == 1
    assert "build-index" in error
