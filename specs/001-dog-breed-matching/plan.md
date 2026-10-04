# Implementation Plan: Dog Breed Matching

**Branch**: `001-dog-breed-matching` | **Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-dog-breed-matching/spec.md` and the technical, organizational, and performance preferences supplied with `/speckit-plan`.

## Summary

Build a local Python web application that serves a lightweight HTML/CSS/JavaScript page and a FastAPI JSON service, with a Python CLI for validating the dataset, building a local image index, and running the service. The application uses only JPG/JPEG photos under the project's `Dog-Breeds-Dataset` as reference images and derives each displayed breed name from the image's parent folder. A locally run CLIP image encoder creates reusable reference-image vectors; a submitted JPG is compared against those vectors, and the closest image, folder title, and a documented integer 1-100% visual-similarity score are returned. No relational database or external image-recognition API is required.

## Technical Context

**Language/Version**: Python 3.11; standard HTML, CSS, and JavaScript.

**Primary Dependencies**: FastAPI and Uvicorn for the same-origin web service; `python-multipart` for uploads; Pillow for safe JPEG decoding; NumPy for indexed vectors; PyTorch and Hugging Face Transformers for the pinned CLIP model. `argparse` provides the CLI without an additional CLI framework.

**Storage**: Read-only `Dog-Breeds-Dataset/` application data (~2.75 GiB and 12,230 JPG/JPEG images in the current checkout, across 356 breed folders). Derived `manifest.json` and `embeddings.npy` live under `.cache/dog-match/` and can be rebuilt. No database stores image blobs. User uploads and match history are not persisted.

**Testing**: pytest, pytest-cov with a strict `>80%` coverage gate, mypy for production Python, FastAPI TestClient integration tests, and browser-flow tests for desktop/mobile and keyboard navigation.

**Target Platform**: Local Python service opened in the latest stable Chrome, Firefox, or Edge on desktop and mobile viewport sizes. Default listener is `127.0.0.1`.

**Project Type**: Single Python web application with a required CLI and a same-origin static frontend.

**Performance Goals**: Page upload control ready within 5 seconds on a connection of at least 25 Mbps download / 5 Mbps upload. Top-match breed-name agreement of at least 80% on the documented 100-photo evaluation sample. The page shell must not transfer the dataset or embedding matrix to the browser.

**Constraints**: Exclusive reference images are local JPG/JPEG files beneath `Dog-Breeds-Dataset/`; breed title comes from the immediate parent folder. Index generation is an explicit CLI operation, not a web-startup task. Initial upload defaults are 10 MiB and 40 megapixels, configurable. Validate decoded image content, not only file name or MIME type. Preserve the included CC BY 4.0 license and provide accurate attribution. CLIP checkpoint is pinned and cached locally; no remote matching API is called. Keep uploaded data request-scoped.

**Scale/Scope**: One photo-upload/match/result workflow; 356 breed folders and approximately 12,230 JPG/JPEG images in the current repository inventory. Social networking and dog adoption are excluded. The measured image count differs from the README's nominal 35-images-per-breed statement, so validation uses actual discovered files.

## Constitution Check

*Gate: pass before research and re-check after design.*

| Principle or constraint | Plan decision | Gate |
|-------------------------|---------------|------|
| Python web app plus CLI | One typed Python package exposes FastAPI and `python -m dog_match` operational commands. | PASS |
| Faithful local matching | Only manifest-indexed local JPG/JPEG images are candidates; result ID resolves to a dataset image, and label is its parent folder title. | PASS |
| Similarity meaning | Normalize cosine similarity to an integer 1-100 display score; describe it as photo similarity, never breed probability. This is within the constitution's stated 0-100 range. | PASS |
| Type hints and tests | Type all production Python; gate with mypy and pytest-cov configured to reject coverage at or below 80%. | PASS |
| Resilient interaction | Validate API response/error states; do not use browser local storage; return safe error messages and never fabricate a result. | PASS |
| Welcoming, simple UI | Use a single static page and native browser controls; avoid frontend frameworks and unnecessary services. | PASS |
| Dataset and scope | Keep the local folder as the exclusive reference source; preserve its license; do not add social or adoption workflows. | PASS |

No constitutional violations require a complexity exception. Re-evaluate the 80% accuracy gate against the held-out photo sample before release; the plan does not claim that the model has already met it.

## Project Structure

### Documentation (this feature)

```text
specs/001-dog-breed-matching/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── cli.md
│   ├── http-api.md
│   └── model-score.md
└── tasks.md                 # Created by /speckit-tasks
```

### Source Code (repository root)

```text
pyproject.toml
src/dog_match/
├── __init__.py
├── __main__.py
├── cli.py                   # serve, validate-dataset, build-index
├── config.py
├── app.py                   # FastAPI routes and static page mounting
├── dataset.py               # Safe traversal and folder-derived labels
├── encoder.py               # Pinned CLIP load and image embeddings
├── index.py                 # Versioned manifest and embedding matrix
├── matcher.py               # Cosine ranking and 1-100 score conversion
└── static/
    ├── index.html
    ├── styles.css
    └── app.js
tests/
├── unit/
├── integration/
└── e2e/
Dog-Breeds-Dataset/          # Existing, read-only reference images and license
.cache/dog-match/            # Generated, ignored manifest and embeddings
```

**Structure Decision**: Use one `src/` Python package because the frontend is a small static page served by the same FastAPI application. Keep the API, CLI, dataset scanner, encoder, index, and matcher as separate modules with direct responsibilities; do not create separate backend/frontend deployments or a relational database. Keep the 2.75-GiB source image set unchanged and the derived feature index rebuildable.

## Complexity Tracking

| Added complexity | Why it is needed | Simpler alternative rejected because |
|------------------|------------------|-------------------------------------|
| Pinned CLIP encoder and generated vector index | Compare more than 12,000 varied photos while pursuing the 80% breed-label target without an external recognition API. | Pixel matching is too sensitive to lighting/background and does not meet the intended breed-similarity use. Validate the accuracy gate before release. |
| Separate CLI index-build operation | Prevent full-dataset decoding and model inference from delaying service startup or page readiness. | Re-indexing at every start repeatedly processes a multi-gigabyte collection. |

## Architecture Preferences

- **Stateless image processing**: Handle each uploaded photo only for its immediate match request. Do not write uploads to application storage, the generated index, logs, browser storage, or a database; release request buffers after responding. The dataset and its derived reference-image index are application data and are not user uploads.
- **Memory-only upload path**: The request size limit is 10 MiB. Configure multipart parsing so files up to that limit remain in memory and cannot roll over to temporary disk. If the selected parser cannot guarantee this, use a bounded streaming parser that rejects over-limit uploads before buffering them. Add a test that verifies upload handling creates no temporary file.
- Keep the current single-process application shape: FastAPI serves the static page and JSON endpoints, while the CLI validates and indexes the local reference collection. Do not add accounts, background services, external image APIs, or a database for uploads.

## Development Requirements

- **Constitutional compliance**: All design and implementation changes MUST be reviewed against `.specify/memory/constitution.md`. Keep the required Python type hints and strictly greater than 80% automated coverage gate; reject changes that violate a constitutional requirement unless the constitution is amended first.
- **Mobile-first layout**: Design the upload and result screens for narrow mobile screens first, then expand for tablet and desktop. Keep content readable, controls reachable, and result information visible without horizontal scrolling.
- **Cross-browser testing**: Test the upload, progress, result, and failure flows in the latest stable Chrome, Firefox, Safari, and Edge releases on desktop and mobile/tablet viewport sizes. Safari is added here by this planning preference; the active feature spec currently names Chrome, Firefox, and Edge, so update the spec before task generation if Safari is a binding acceptance requirement.
- Retain automated unit, API integration, and browser-flow checks, with all production Python type-checked and coverage strictly above 80%.

## Security Requirements

- **Validate image content before decoding**: Enforce the request byte limit while receiving the body; ignore the client filename as a storage path and do not trust the declared media type or `.jpg` extension. Check JPEG signatures and require Pillow to verify and fully decode the image before passing it to the encoder. Reopen after verification, apply orientation, convert to RGB, and reject decode errors with a user-safe response.
- Enforce the existing 40-megapixel decoded-image limit to reduce decompression-bomb and resource-exhaustion risk. Keep Pillow and model dependencies pinned to maintained versions and surface malformed-image failures without exposing stack traces.
- **Privacy**: Do not create user accounts, collect personal details, retain uploads, or log image contents or raw filenames. Keep uploaded pixels and metadata in bounded request memory only, discard them after the response, and ensure error paths release buffers too.
- Serve locally on `127.0.0.1` by default. Keep user-facing errors actionable and internal diagnostics out of API responses.

## Platform Requirements

- The application MUST run in modern desktop and mobile browsers without requiring plugins or browser extensions.
- In addition to the browsers listed in the feature spec, include the latest stable Safari release in the planned compatibility matrix. Validate desktop, tablet, and mobile viewport layouts, including upload selection and result-image display.
- Keep the frontend as standard HTML, CSS, and JavaScript served from the same origin; no client-side framework or browser add-on is required.
