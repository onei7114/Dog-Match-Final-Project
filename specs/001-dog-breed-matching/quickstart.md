# Quickstart and Validation

## Prerequisites

- Python 3.11 or later supported by the pinned project dependencies.
- The project-local `Dog-Breeds-Dataset/` folder (about 2.75 GiB of JPG/JPEG data in the current checkout).
- Network access for the first download of the pinned CLIP checkpoint, unless the checkpoint is already cached or provisioned locally. Runtime image matching itself does not call an external service.

## Install and Build the Local Index

From the repository root in PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,model]"
.\.venv\Scripts\python.exe -m dog_match validate-dataset --dataset .\Dog-Breeds-Dataset
.\.venv\Scripts\python.exe -m dog_match build-index --dataset .\Dog-Breeds-Dataset --cache-dir .\.cache\dog-match
```

Dataset validation reports discovered folders, usable JPG/JPEG images, empty folders, and decode failures. Index building can take significant time because it processes the local image collection; it is an operator action, not a web-server startup task.

## Run the Application

```powershell
.\.venv\Scripts\python.exe -m dog_match serve --dataset .\Dog-Breeds-Dataset --cache-dir .\.cache\dog-match --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`. The page should show an upload control within five seconds on a connection meeting the spec's broadband condition. Submit a valid JPG and confirm the response shows one collection image, its parent-folder breed title, and a 1-100% visual similarity score. No uploaded photo should remain on disk after the request.

## Automated Validation

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=dog_match --cov-report=term-missing --cov-fail-under=80.1
.\.venv\Scripts\python.exe -m mypy src\dog_match
```

The coverage threshold is strictly greater than 80%. Add browser-flow checks for current stable Chrome, Firefox, and Edge, desktop/mobile viewports, upload validation, API failure messaging, and keyboard access.

## Acceptance Checks

1. Select at least 100 labeled JPG photos, remove the entire selected sample from the reference candidates for all predictions, and verify at least 80% folder-name agreement; record the sample and scoring method.
2. Verify every successful result has a collection image, its exact parent folder title, and an integer score from 1% through 100%; confirm the score is not described as breed probability.
3. Test corrupt, unsupported, oversized, and missing uploads; verify recoverable messages and no fabricated result.
4. Test missing, stale, empty, and partially unreadable dataset/index states; verify actionable operator guidance and no false readiness.
5. Measure page-shell readiness from opening the site to the upload control being usable under at least 25 Mbps download and 5 Mbps upload conditions; the limit is five seconds.
6. Review dataset attribution in the page and documentation and preserve the included license/README files.
