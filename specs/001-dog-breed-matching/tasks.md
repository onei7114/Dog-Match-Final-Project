# Tasks: Dog Breed Matching

**Input**: Design documents from `specs/001-dog-breed-matching/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, and `quickstart.md`

**MVP focus**: Build the local reference-image index, compare an uploaded JPG against it, and display the closest image, its folder-derived breed name, and a 1-100% visual-similarity score. The “database” is the local dataset plus a rebuildable vector index; do not create a relational database or copy image blobs.

**Task sizing**: Each task is scoped for approximately 1-3 hours. Build work is grouped into the four requested phases. Story labels keep the P1 and P2 deliverables traceable.

## Phase 1: Foundation (API Setup and Data Models)

**Purpose**: Set up the Python application, safe dataset access, reusable index, and shared upload boundary.

- [X] T001 [P] Create `pyproject.toml` with Python 3.11 package metadata and FastAPI, Uvicorn, python-multipart, Pillow, NumPy, PyTorch, Transformers, pytest, pytest-cov, and mypy dependencies; Acceptance: editable install resolves all declared dependencies and coverage is configured to fail at or below 80%.
- [X] T002 [P] Create the `src/dog_match/` package skeleton in `src/dog_match/__init__.py` and `src/dog_match/__main__.py`; Acceptance: the package imports without errors, and CLI help is verified after T016.
- [X] T003 Add typed runtime settings for dataset root, cache directory, upload byte limit, decoded-pixel limit, and host/port in `src/dog_match/config.py`; Acceptance: defaults match the plan (10 MiB, 40 megapixels, loopback host) and invalid paths/limits fail with actionable configuration errors.
- [X] T004 [P] Implement recursive JPG/JPEG discovery and parent-folder breed labels in `src/dog_match/dataset.py`; Acceptance: paths stay beneath the configured root, labels equal immediate parent folder titles, and unreadable/non-image files are reported rather than indexed.
- [X] T005 Define typed index-manifest and breed-photo records in `src/dog_match/index.py`; Acceptance: each indexed row contains the opaque reference ID, root-relative path, folder title, file size, modification time, model revision, and preprocessing version required by `data-model.md`.
- [X] T006 [P] Implement a pinned local CLIP image encoder and normalized image-vector interface in `src/dog_match/encoder.py`; Acceptance: the wrapper converts decoded images to model inputs, returns finite unit-length vectors, and never sends photos to a remote service.
- [X] T007 [P] Implement bounded, memory-only JPEG upload validation in `src/dog_match/upload_validation.py`; Acceptance: reject oversized byte streams and images above 40 megapixels before matching, verify actual JPEG content and full decode rather than trusting filename/MIME type, and create no temporary file.
- [X] T008 Create the FastAPI application factory and non-sensitive readiness response in `src/dog_match/app.py`; Acceptance: the app can be imported by tests, reports ready only when its configured index is loaded, and does not expose local filesystem paths.

## Phase 2: Business Logic (Build the Comparable Reference Index)

**Purpose**: Make the local collection searchable and implement the closest-photo comparison. This is the core “database” work for the MVP.

- [X] T009 [P] [US1] Implement normalized cosine ranking, deterministic tie-breaking, and the documented integer score conversion in `src/dog_match/matcher.py`; Acceptance: select the greatest unrounded cosine value, break exact ties by normalized relative path, and return an integer 1-100 score without treating it as breed probability.
- [X] T010 [P] [US1] Implement atomic index creation and compatibility checks for the manifest and embedding matrix in `src/dog_match/index.py`; Acceptance: index rows align with vectors, writes replace the previous index only after a complete build, and model/preprocessing/inventory mismatches require a rebuild.
- [X] T011 [US1] Create a reproducible 100-photo accuracy evaluation runner in `scripts/evaluate_matching.py`; Acceptance: the entire test sample is excluded from all reference candidates, the report records sampling/exclusions and folder-label agreement, and success requires at least 80 correct labels out of 100.

## Phase 3: UI Components (API, CLI Commands, and Result Presentation)

**Purpose**: Connect the index to the standalone user flow and the required operator commands.

- [X] T012 [US1] Define typed match, health, and error response schemas in `src/dog_match/schemas.py`; Acceptance: response fields and status/error codes match `contracts/http-api.md`, and similarity is an integer from 1 through 100.
- [X] T013 [US1] Implement `POST /api/v1/matches` in `src/dog_match/app.py`; Acceptance: valid in-memory JPG uploads invoke the matcher and return the selected breed folder title, score, safe reference URL, and disclaimer without persisting the uploaded photo.
- [X] T014 [US1] Implement `GET /api/v1/reference-images/{reference_id}` using the validated manifest in `src/dog_match/app.py`; Acceptance: only known opaque IDs resolve, returned files remain beneath the dataset root, and arbitrary IDs cannot become filesystem paths.
- [X] T015 [US1] Implement `validate-dataset` and `build-index` commands in `src/dog_match/cli.py`; Acceptance: validation reports actual discovered counts/errors without modifying source images, and indexing batch-encodes JPGs into the cache without copying image blobs.
- [X] T016 [US1] Implement the `serve` CLI command and register `python -m dog_match` options in `src/dog_match/cli.py` and `src/dog_match/__main__.py`; Acceptance: local serving defaults to `127.0.0.1:8000`, accepts explicit dataset/cache/host/port settings, and refuses readiness with rebuild guidance if the index is missing or stale.
- [X] T017 [US1] Create the standalone upload/result page in `src/dog_match/static/index.html`; Acceptance: the page contains a labeled JPG upload control, submit action, progress region, result region, and recoverable message region with no account workflow.
- [X] T018 [P] [US1] Add mobile-first responsive styles in `src/dog_match/static/styles.css`; Acceptance: upload and result layouts fit mobile, tablet, and desktop widths without horizontal scrolling, overlapping content, or unreadable controls.
- [X] T019 [US1] Implement the successful upload-to-result browser flow in `src/dog_match/static/app.js`; Acceptance: submit one JPG to the match endpoint, render only the returned reference image/folder title/score/disclaimer, and never display the score as breed probability.
- [X] T020 [US1] Mount the static page and assets at the same origin in `src/dog_match/app.py`; Acceptance: `GET /` serves the standalone page and the browser does not download the dataset or embedding matrix.

## Phase 4: Testing & Polish (Errors, Privacy, Coverage, and Documentation)

**Purpose**: Verify both user stories, enforce privacy/security requirements, validate the accuracy and browser targets, and document operation.

### User Story 1 - Get a Breed Match (P1)

**Independent test**: With a built local index, submit a valid JPG and verify that the highest-scoring dataset image, its exact parent-folder title, and a 1-100% photo-similarity score are displayed.

- [X] T021 [P] [US1] Add dataset-discovery and manifest/index unit tests in `tests/unit/test_dataset.py` and `tests/unit/test_index.py`; Acceptance: cover folder-derived labels, JPG filtering, unreadable files, stale-index detection, and atomic-write failure without mutating the dataset.
- [X] T022 [P] [US1] Add matcher and score unit tests in `tests/unit/test_matcher.py`; Acceptance: cover cosine ranking, normalized vectors, deterministic ties, score endpoints/rounding, and the 1-100 integer range.
- [X] T023 [US1] Add successful match and reference-image API tests in `tests/integration/test_match_api.py`; Acceptance: verify response fields, folder title provenance, selected reference bytes, same-origin URL, and no upload persistence.
- [X] T024 [US1] Add an end-to-end happy-path browser test in `tests/e2e/test_match_flow.py`; Acceptance: a user can upload a valid JPG, see the matching image and breed-folder title, and understand the score as visual similarity.

### User Story 2 - Recover from an Upload or Matching Problem (P2)

**Independent test**: Submit invalid images and simulate unavailable matching data; verify actionable errors, no fabricated result, and the ability to retry with another photo.

- [X] T025 [US2] Map upload, decode, index, and matcher failures to the documented safe API errors in `src/dog_match/app.py` and `src/dog_match/schemas.py`; Acceptance: missing, oversized, invalid-JPEG, unavailable-index, and unexpected failures return the documented codes/messages without stack traces.
- [X] T026 [US2] Add frontend progress, error, empty, and retry states in `src/dog_match/static/app.js` and `src/dog_match/static/index.html`; Acceptance: failed requests clear/replace stale results, explain how to recover, and allow a new photo submission.
- [X] T027 [P] [US2] Add upload-validation and privacy tests in `tests/unit/test_upload_validation.py`; Acceptance: spoofed extension/MIME, corrupt JPEG, over-byte-limit, over-pixel-limit, parser exception, and normal/error cleanup cases are covered, and tests confirm no temporary upload file or retained image is created.
- [X] T028 [US2] Add failure-path API tests in `tests/integration/test_match_errors.py`; Acceptance: missing upload, unsupported/corrupt image, unavailable/empty index, and matcher exception produce actionable responses and never fabricate a breed, image, or score.
- [ ] T029 [P] [US2] Add keyboard and cross-browser flow checks in `tests/e2e/test_match_flow.py`; Acceptance: upload, progress, result, and error flows are operable and readable on desktop/mobile viewports in latest stable Chromium, Firefox, Edge, and WebKit. Confirm native Safari on a macOS test host before release browser certification.

### Cross-Cutting Release Checks

- [X] T030 Add the strict coverage and type-check commands to project configuration in `pyproject.toml`; Acceptance: CI/local commands fail unless pytest coverage is strictly greater than 80% and production modules pass mypy.
- [X] T031 Run the documented 100-photo accuracy evaluation and record results in `specs/001-dog-breed-matching/accuracy-evaluation.md`; Acceptance: document sample selection/exclusions, model revision, count, and agreement rate; block MVP release if fewer than 80 labels match.
- [X] T032 Update `README.md` with install/index/serve instructions, upload privacy, score limitations, and dataset attribution; Acceptance: a new operator can follow the documented CLI flow, the CC BY 4.0 attribution/license is preserved, and no claim implies guaranteed breed identification.
- [X] T033 Run the end-to-end quickstart and performance check in `specs/001-dog-breed-matching/quickstart.md`; Acceptance: the page upload control is ready within five seconds at 25 Mbps down/5 Mbps up, no plugin/extension is needed, and result/error flows match the contracts.

## Dependencies and Execution Order

### Phase Dependencies

- **Phase 1 Foundation**: T001-T008 establish packaging, configuration, dataset/index types, encoder, safe upload boundary, and app bootstrap. T001-T002 can run in parallel; after T003, T004/T006/T007 can run in parallel.
- **Phase 2 Business Logic**: T009-T011 depend on the Phase 1 data/encoder interfaces. T009 is the prerequisite for evaluation in T011; T010 supplies the index used by runtime matching.
- **Phase 3 UI Components**: T012-T020 depend on the result schema and matcher. The API and CLI need the index; the static frontend can be developed alongside CLI work after T017 establishes element IDs.
- **Phase 4 Testing & Polish**: T021-T024 validate P1; T025-T029 validate P2. T030-T033 are release gates and documentation; T031 requires a complete generated index and cannot be considered passed until the 100-photo evaluation is run.

### User Story Dependencies

- **US1 (P1)**: Depends on Foundation and the Business Logic index/matcher; delivers the MVP upload-to-match flow.
- **US2 (P2)**: Reuses the upload/API/UI surfaces from US1 and adds recoverable invalid-input and unavailable-index behavior; testable after those shared surfaces exist.

### Task Dependencies

| Task | Depends on |
|------|------------|
| T001-T002 | None; independent setup tasks. |
| T003 | T001-T002. |
| T004, T006-T007 | T003. |
| T005 | T004. |
| T008 | T003, T005. |
| T009 | T005-T006. |
| T010 | T004-T006. |
| T011 | T009-T010. |
| T012 | T008-T009. |
| T013 | T007-T009, T012. |
| T014 | T005, T008, T012. |
| T015 | T004-T006, T010. |
| T016 | T008, T015. |
| T017 | T001-T002. |
| T018 | T017. |
| T019 | T012-T013, T017. |
| T020 | T013-T014, T017-T019. |
| T021 | T004-T005. |
| T022 | T009. |
| T023 | T013-T014, T020. |
| T024 | T019-T020, T023. |
| T025 | T007, T012-T013. |
| T026 | T019, T025. |
| T027 | T007, T025. |
| T028 | T025-T027. |
| T029 | T024, T028. |
| T030 | T001, T021-T029. |
| T031 | T011, T015. |
| T032 | T015-T016, T025-T031. |
| T033 | T014-T020, T028-T031. |

### Parallel Opportunities

- **Foundation**: T001 and T002 are independent; after T003, dataset scanning (T004), encoder setup (T006), and upload validation (T007) touch separate modules.
- **Business Logic**: T009 and T010 can proceed in parallel after their shared data/vector contracts are agreed; T011 follows T009/T010.
- **UI**: After T017, CSS work (T018) can proceed separately from CLI commands (T015-T016); static page integration (T020) follows the API/page assets.
- **Testing**: T021, T022, and T027 operate on separate test files and can run in parallel after their corresponding modules exist; browser suites run after API and page integration.

## MVP Implementation Strategy

1. Complete Phase 1 and build the index with Phase 2.
2. Complete the P1 match path in Phase 3 and its tests T021-T024.
3. **Stop and validate the MVP**: show one matching image, its parent-folder breed title, and a documented 1-100% visual-similarity score; run the held-out accuracy gate before claiming the 80% target.
4. Complete P2 failure/privacy handling, browser matrix, coverage/type gates, documentation, and five-second readiness checks in Phase 4.

## Notes

- The local JPG folder tree is the only reference collection; no relational database is planned.
- User uploads are memory-only and ephemeral. Keep index/cache paths separate from the reference dataset and never include user images in the generated index.
- The recorded accuracy result is 38/100 (38%), below the required 80%; the MVP is not release-ready until a revised local matching approach meets the gate.
- The cross-browser flow passed in Chromium, Firefox, Edge, and WebKit on this Windows host; native Safari remains to be verified on macOS.
- `[P]` means the task touches an independent file/module and has no dependency on an incomplete task. `[US1]` and `[US2]` map to the P1 and P2 stories in `spec.md`.
- Safari is an added plan preference beyond the current spec's Chrome/Firefox/Edge list; update `spec.md` if this is a binding acceptance requirement.
