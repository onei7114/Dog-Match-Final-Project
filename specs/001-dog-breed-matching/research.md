# Research: Dog Breed Matching

## Dataset Inventory and Handling

**Decision**: Treat `Dog-Breeds-Dataset/` as a read-only, local application dependency. Traverse JPG/JPEG files recursively and derive each breed name from the immediate parent folder. Store only image paths and generated feature vectors in the search index; do not duplicate source images into a database or send the collection to browsers.

**Rationale**: The local inventory contains 356 breed folders, 12,230 JPG/JPEG images, and approximately 2.75 GiB of image data. The dataset README describes 35 images per breed and 5.32 GB uncompressed; the measured JPG count does not equal 356 x 35, so indexing must use discovered files rather than assume a fixed count. A precomputed index keeps the 5-second page-ready target independent of model initialization and whole-dataset traversal.

**Alternatives considered**:
- Relational database containing copied image blobs: rejected because the existing filesystem is the mandated reference source and copying about 2.75 GiB adds storage and update complexity.
- Send the full collection to the browser: rejected because it would violate the page load target and waste bandwidth.

## Image Comparison

**Decision**: Use a pinned local CLIP image encoder (`openai/clip-vit-base-patch32` through Hugging Face Transformers) to create normalized image embeddings. Compare the uploaded image embedding with precomputed embeddings using cosine similarity and select the highest-scoring image. Keep the model and inference local; no image-matching API or external image source is used.

**Rationale**: Raw pixel difference is sensitive to lighting, framing, and background. CLIP provides a pretrained image representation and processor; the official Transformers documentation exposes projected image embeddings and documents image resizing and normalization. A local embedding comparison is more suitable for varied photos and 356 labels than an exact-pixel comparison.

**Alternatives considered**:
- Pixel/color histograms: rejected as too sensitive to image conditions and not a credible path to the 80% breed-label target.
- External hosted recognition API: rejected because the local dataset must remain the exclusive reference collection and external image processing would add cost, privacy, availability, and network dependencies.
- Train a new classifier from scratch: rejected because approximately 35 images per breed is a small training set and would add substantial training and model-maintenance work.

**Accuracy gate**: This model choice is a candidate, not a claim that 80% accuracy is already achieved. Before accepting it, select at least 100 photos with known labels, remove the entire selected sample from the reference candidates, and evaluate each photo against the remaining collection. Require at least 80% agreement. If it fails, compare an alternative feature encoder or preprocessing within the same local matching design before release.

## Similarity Score

**Decision**: Normalize CLIP image vectors, take their cosine similarity, and map the value linearly from the cosine range `[-1, 1]` to an integer score in `[1, 100]`, clamping endpoints. Return the highest-scoring reference photo and its immediate parent folder title. Label the number as a photo-similarity score, never as the probability that the breed label is correct.

**Rationale**: A deterministic mapping satisfies the requested integer scale and is straightforward to test. The score is a display normalization of a model similarity value, not a calibrated confidence or probability; this limitation must be explained in the UI and project documentation.

**Alternatives considered**:
- Softmax across dataset images: rejected because the resulting values depend on the number and composition of reference images and can be misread as breed probability.
- Return raw cosine as a percentage: rejected because cosine is not naturally a 0-to-100 percentage.

## Upload and API

**Decision**: Use FastAPI `UploadFile` with `python-multipart` for one JPG upload per match request. Stream/cap the request, verify that the bytes decode as a JPEG with Pillow, normalize orientation, enforce a configurable size and pixel limit, and never trust the client filename or declared MIME type alone. Keep the API and static page same-origin.

**Rationale**: FastAPI documents `UploadFile` as a spooled file suitable for larger inputs, unlike accepting the whole file as an in-memory `bytes` value. Same-origin delivery avoids unnecessary CORS configuration. Validation limits reduce memory and decompression-bomb risks.

**Initial limits**: 10 MiB per upload and 40 megapixels maximum decoded dimensions, configurable through application settings. Return a clear 413 for an oversized file and a clear 415 for unsupported or invalid image content.

**Alternatives considered**:
- Accept file bytes directly in a request parameter: rejected because it stores the complete upload in memory.
- Persist uploaded photos: rejected because the spec assumes photos are used for the current result and not retained.

## Index Lifecycle and Startup

**Decision**: Add a CLI index-build operation that scans the local dataset, validates images, computes embeddings in batches, and atomically writes a versioned manifest and numeric embedding matrix under an application cache directory. At startup, load a compatible index; fail readiness with actionable CLI guidance if the index is missing, stale, or incompatible. Provide a dataset-validation CLI command that reports folders, readable image counts, bad files, and empty folders.

**Rationale**: The dataset is large enough that walking and encoding every image at each web-server startup would be slow. The index stores relative paths, folder-derived labels, file size/mtime metadata, model identifier/revision, preprocessing version, and embedding rows. Startup can validate the manifest and stat listed files without decoding the collection. Atomic replacement avoids partial indexes after interruption.

**Index invalidation**: Rebuild when the configured model/revision, preprocessing version, or discovered path/size/mtime inventory changes. CLI rebuild remains an explicit operation so web requests never block on full-dataset indexing.

## CLI and Runtime

**Decision**: Expose an `argparse`-based `python -m dog_match` entry point with `serve`, `validate-dataset`, and `build-index` commands. Default the local server to `127.0.0.1`; allow host, port, dataset path, and cache path to be configured explicitly.

**Rationale**: `argparse` meets the required operational CLI with no extra command-framework dependency. A loopback default fits a local standalone web application and avoids unintentionally exposing an unauthenticated upload service to a network.

## Quality Gates

**Decision**: Use pytest and pytest-cov for automated tests, with the coverage gate configured to fail at 80% or less. Add type checking for production Python and browser-flow checks for desktop, mobile, and keyboard navigation.

**Rationale**: The constitution requires type hints and strictly greater than 80% coverage. Unit tests cover data parsing, embedding-score math, validation, and response mapping; API tests cover upload/error responses; end-to-end checks cover the user journey and responsive behavior.

## Dataset Attribution

**Decision**: Preserve the dataset's included `LICENSE` and `README.md`, and include an attribution notice in project documentation and the page's about/footer area where appropriate. Confirm the dataset source/author details from the project metadata before publication; do not infer that all image copyrights belong to FCI merely because the dataset describes FCI breeds.

**Rationale**: The included license is Creative Commons Attribution 4.0. Attribution must be handled, and rights to individual images should not be overstated.

## Sources

- FastAPI, “Request Files”: https://fastapi.tiangolo.com/tutorial/request-files/ — `UploadFile` spooling, form uploads, and `python-multipart` prerequisite.
- Hugging Face Transformers, “CLIP”: https://huggingface.co/docs/transformers/model_doc/clip — image processor normalization and projected image embeddings.
- Local inventory: `Dog-Breeds-Dataset/README.md`, `Dog-Breeds-Dataset/LICENSE`, and a recursive count of JPG/JPEG files under `Dog-Breeds-Dataset/`.
