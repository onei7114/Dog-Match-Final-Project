"""Operational CLI for dataset validation, index building, and local serving."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import uvicorn

from dog_match.app import create_app
from dog_match.config import Settings
from dog_match.dataset import scan_dataset
from dog_match.encoder import ClipImageEncoder, PREPROCESSING_VERSION
from dog_match.index import IndexUnavailableError, build_index, load_index


def _settings(args: argparse.Namespace) -> Settings:
    settings = Settings.from_environment()
    return replace(
        settings,
        dataset_root=Path(args.dataset).expanduser() if args.dataset else settings.dataset_root,
        cache_dir=Path(args.cache_dir).expanduser() if args.cache_dir else settings.cache_dir,
        host=args.host if getattr(args, "host", None) else settings.host,
        port=args.port if getattr(args, "port", None) else settings.port,
    )


def _add_paths(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dataset", default=None, help="Local Dog-Breeds-Dataset path")
    parser.add_argument("--cache-dir", default=None, help="Generated index/cache directory")


def _validate_dataset(args: argparse.Namespace) -> int:
    settings = _settings(args)
    scan = scan_dataset(settings.dataset_root)
    report = {
        "breed_folder_count": scan.breed_count,
        "readable_jpeg_count": scan.image_count,
        "empty_breed_folders": list(scan.empty_breed_folders),
        "issues": [
            {"relative_path": issue.relative_path, "reason": issue.reason}
            for issue in scan.issues
        ],
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if scan.image_count else 1


def _build_index(args: argparse.Namespace) -> int:
    settings = _settings(args)
    encoder = ClipImageEncoder.from_pretrained(
        model_id=settings.model_id,
        revision=settings.model_revision,
    )
    manifest = build_index(
        dataset_root=settings.dataset_root,
        cache_dir=settings.cache_dir,
        encoder=encoder,
        batch_size=args.batch_size,
        preprocessing_version=PREPROCESSING_VERSION,
    )
    print(
        json.dumps(
            {
                "breed_count": len({image.breed_name for image in manifest.images}),
                "reference_image_count": manifest.image_count,
                "cache_dir": str(settings.cache_dir),
                "model_id": manifest.model_id,
                "model_revision": manifest.model_revision,
            },
            indent=2,
        )
    )
    return 0


def _serve(args: argparse.Namespace) -> int:
    settings = _settings(args)
    try:
        search_index = load_index(
            settings.cache_dir,
            settings.dataset_root,
            settings.model_id,
            settings.model_revision,
            PREPROCESSING_VERSION,
        )
        encoder = ClipImageEncoder.from_pretrained(
            model_id=settings.model_id,
            revision=settings.model_revision,
            local_files_only=True,
        )
    except (IndexUnavailableError, ImportError, OSError, ValueError) as exc:
        print(f"Cannot start dog-match: {exc}", file=sys.stderr)
        print("Run `python -m dog_match build-index` first.", file=sys.stderr)
        return 1

    app = create_app(settings=settings, search_index=search_index, encoder=encoder)
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dog-match", description="Local dog-breed photo matching")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate-dataset", help="Check local reference photos")
    _add_paths(validate_parser)
    validate_parser.set_defaults(handler=_validate_dataset)

    index_parser = subparsers.add_parser("build-index", help="Build local CLIP image vectors")
    _add_paths(index_parser)
    index_parser.add_argument("--batch-size", type=int, default=16)
    index_parser.set_defaults(handler=_build_index)

    serve_parser = subparsers.add_parser("serve", help="Run the local web application")
    _add_paths(serve_parser)
    serve_parser.add_argument("--host", default=None)
    serve_parser.add_argument("--port", type=int, default=None)
    serve_parser.set_defaults(handler=_serve)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (ImportError, OSError, ValueError, RuntimeError) as exc:
        print(f"dog-match: {exc}", file=sys.stderr)
        return 1
