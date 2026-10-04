# CLI Contract

Entry point: `python -m dog_match` (installed console command: `dog-match`). Commands return exit code `0` on success and nonzero on invalid configuration, invalid dataset, unavailable model/index, or server failure. Diagnostics go to stderr; machine-readable reports may be written with an explicit output option.

## `validate-dataset`

```text
python -m dog_match validate-dataset --dataset Dog-Breeds-Dataset
```

Recursively scan JPG/JPEG images, derive labels from immediate parent folder titles, and report folder count, readable image count, empty folders, and invalid/unreadable files. This command never changes dataset files.

## `build-index`

```text
python -m dog_match build-index --dataset Dog-Breeds-Dataset --cache-dir .cache/dog-match
```

Validate the dataset, create normalized embeddings in batches, and atomically replace the manifest and matrix only after a complete successful build. Include model revision and preprocessing version in the manifest. Print image counts and cache output location; never copy the source image files into the index.

## `serve`

```text
python -m dog_match serve --dataset Dog-Breeds-Dataset --cache-dir .cache/dog-match --host 127.0.0.1 --port 8000
```

Start the local FastAPI application. Defaults bind to `127.0.0.1:8000`. An absent or stale index produces a clear error directing the operator to `build-index`; serving does not trigger a complete image scan or embedding build.

All commands accept explicit dataset/cache paths. Environment-variable defaults may be added for deployment, but command-line arguments take precedence and are shown in `--help`.
