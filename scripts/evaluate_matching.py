"""Evaluate top-match breed labels on a deterministic held-out photo sample."""

from __future__ import annotations

import argparse
import random
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageOps

from dog_match.config import Settings
from dog_match.encoder import ClipImageEncoder, PREPROCESSING_VERSION
from dog_match.index import IndexUnavailableError, ReferenceIndex, load_index
from dog_match.matcher import find_closest_reference


def exclude_evaluation_set(index: ReferenceIndex, evaluation_ids: set[str]) -> ReferenceIndex:
    """Remove the entire evaluation sample from the candidate reference set."""
    indexed_ids = {image.reference_id for image in index.manifest.images}
    missing_ids = evaluation_ids - indexed_ids
    if missing_ids:
        raise ValueError("Evaluation photos are missing from the current index; rebuild it")
    keep_positions = [
        position
        for position, image in enumerate(index.manifest.images)
        if image.reference_id not in evaluation_ids
    ]
    if not keep_positions:
        raise ValueError("No reference images remain after excluding the evaluation set")
    images = tuple(index.manifest.images[position] for position in keep_positions)
    vectors = np.asarray(index.embeddings[keep_positions], dtype=np.float32)
    manifest = replace(
        index.manifest,
        image_count=len(images),
        embedding_dimension=int(vectors.shape[1]),
        images=images,
    )
    return ReferenceIndex(manifest=manifest, embeddings=vectors)


def compare_breed_strategies(
    index: ReferenceIndex,
    uploaded_vector: NDArray[np.float32],
) -> dict[str, str]:
    """Compare photo-neighbor, breed-centroid, and local top-10 vote predictions."""
    query = np.asarray(uploaded_vector, dtype=np.float32).reshape(-1)
    query_norm = float(np.linalg.norm(query))
    if query_norm == 0 or not np.isfinite(query).all():
        raise ValueError("Uploaded image vector is invalid")
    query /= query_norm
    scores = np.asarray(index.embeddings @ query, dtype=np.float32)
    grouped_positions: dict[str, list[int]] = defaultdict(list)
    for position, image in enumerate(index.manifest.images):
        grouped_positions[image.breed_name].append(position)

    top_photo_position = min(
        range(len(index.manifest.images)),
        key=lambda position: (-float(scores[position]), index.manifest.images[position].relative_path),
    )
    top_photo_breed = index.manifest.images[top_photo_position].breed_name

    breed_names = sorted(grouped_positions)
    centroids: list[NDArray[np.float32]] = []
    top_five_means: dict[str, float] = {}
    for breed_name in breed_names:
        positions = grouped_positions[breed_name]
        centroid = np.asarray(index.embeddings[positions].mean(axis=0), dtype=np.float32)
        centroid_norm = float(np.linalg.norm(centroid))
        centroids.append(centroid / centroid_norm if centroid_norm else centroid)
        breed_scores = np.sort(scores[positions])
        top_five_means[breed_name] = float(breed_scores[-min(5, len(positions)) :].mean())
    centroid_scores = np.asarray(centroids, dtype=np.float32) @ query
    centroid_breed = min(
        range(len(breed_names)),
        key=lambda position: (-float(centroid_scores[position]), breed_names[position]),
    )
    top_five_breed = min(breed_names, key=lambda name: (-top_five_means[name], name))

    top_positions = sorted(
        range(len(index.manifest.images)),
        key=lambda position: (-float(scores[position]), index.manifest.images[position].relative_path),
    )[: min(10, len(index.manifest.images))]
    votes = Counter(index.manifest.images[position].breed_name for position in top_positions)
    vote_scores: dict[str, float] = defaultdict(float)
    for position in top_positions:
        vote_scores[index.manifest.images[position].breed_name] += float(scores[position])
    vote_breed = min(votes, key=lambda name: (-votes[name], -vote_scores[name], name))

    return {
        "nearest_photo": top_photo_breed,
        "breed_centroid": breed_names[centroid_breed],
        "breed_top5_mean": top_five_breed,
        "top10_vote": vote_breed,
    }


def evaluate(
    sample_size: int,
    seed: int,
    dataset_root: Path,
    cache_dir: Path,
) -> tuple[int, int, list[tuple[str, str, bool]], str, str, dict[str, int]]:
    if sample_size < 100:
        raise ValueError("The accuracy gate requires at least 100 evaluation photos")
    settings = Settings.from_environment()
    reference_index = load_index(
        cache_dir,
        dataset_root,
        settings.model_id,
        settings.model_revision,
        PREPROCESSING_VERSION,
    )
    if sample_size > reference_index.image_count:
        raise ValueError(
            f"Requested {sample_size} photos, but the index has only {reference_index.image_count} readable images"
        )
    encoder = ClipImageEncoder.from_pretrained(
        model_id=reference_index.manifest.model_id,
        revision=reference_index.manifest.model_revision,
        local_files_only=True,
    )
    sample = random.Random(seed).sample(list(reference_index.manifest.images), sample_size)
    evaluation_index = exclude_evaluation_set(
        reference_index,
        {record.reference_id for record in sample},
    )
    correct = 0
    rows: list[tuple[str, str, bool]] = []
    strategy_correct: dict[str, int] = {
        "nearest_photo": 0,
        "breed_centroid": 0,
        "breed_top5_mean": 0,
        "top10_vote": 0,
    }
    root = dataset_root.resolve(strict=True)
    for record in sample:
        with Image.open(root / record.relative_path) as image:
            image.load()
            oriented = ImageOps.exif_transpose(image)
            rgb_image = (oriented if oriented is not None else image).convert("RGB")
        try:
            vector = encoder.encode([rgb_image])[0]
        finally:
            rgb_image.close()
        match = find_closest_reference(evaluation_index, vector)
        strategy_predictions = compare_breed_strategies(evaluation_index, vector)
        is_correct = match.breed_name == record.breed_name
        correct += int(is_correct)
        for strategy_name, predicted_breed in strategy_predictions.items():
            strategy_correct[strategy_name] += int(predicted_breed == record.breed_name)
        rows.append((record.relative_path, match.breed_name, is_correct))
    return (
        correct,
        sample_size,
        rows,
        reference_index.manifest.model_id,
        reference_index.manifest.model_revision,
        strategy_correct,
    )


def write_report(
    output_path: Path,
    correct: int,
    total: int,
    rows: list[tuple[str, str, bool]],
    seed: int,
    model_id: str,
    model_revision: str,
    strategy_correct: dict[str, int],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    percent = correct / total * 100
    lines = [
        "# Dog Match Accuracy Evaluation",
        "",
        f"- Sample size: {total}",
        f"- Random seed: {seed}",
        f"- Model: `{model_id}` at revision `{model_revision}`",
        "- Sampling: deterministic sample from readable JPG/JPEG files in the local dataset.",
        "- Exclusion: all evaluation photos are omitted from every prediction's reference candidates; other images from the same breed folder remain eligible.",
        f"- Correct top-folder labels: {correct}/{total} ({percent:.1f}%)",
        f"- Release gate (at least 80%): {'PASS' if correct / total >= 0.8 else 'FAIL'}",
        "",
        "## Local-only strategy comparison",
        "",
        "The image-to-image result remains the production baseline until an alternative is explicitly adopted and its score semantics are documented.",
        "",
        "| Strategy | Correct folder labels | Agreement |",
        "|---|---:|---:|",
    ]
    lines.extend(
        f"| {strategy_name} | {strategy_count}/{total} | {strategy_count / total:.1%} |"
        for strategy_name, strategy_count in strategy_correct.items()
    )
    lines.extend([
        "",
        "| Evaluation photo (relative path) | Selected breed folder | Correct |",
        "|---|---|---:|",
    ])
    lines.extend(
        f"| `{path}` | {breed} | {'yes' if is_correct else 'no'} |"
        for path, breed, is_correct in rows
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("Dog-Breeds-Dataset"))
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache/dog-match"))
    parser.add_argument("--sample-size", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("specs/001-dog-breed-matching/accuracy-evaluation.md"),
    )
    args = parser.parse_args()
    try:
        correct, total, rows, model_id, model_revision, strategy_correct = evaluate(
            args.sample_size,
            args.seed,
            args.dataset,
            args.cache_dir,
        )
    except (OSError, ValueError, IndexUnavailableError) as exc:
        parser.error(str(exc))
    write_report(args.output, correct, total, rows, args.seed, model_id, model_revision, strategy_correct)
    print(f"Accuracy: {correct}/{total} ({correct / total:.1%}); report: {args.output}")
    return 0 if correct / total >= 0.8 else 1


if __name__ == "__main__":
    raise SystemExit(main())
