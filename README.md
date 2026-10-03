# Dog Match

Dog Match is a local web application that compares one uploaded JPG/JPEG photo with the project's `Dog-Breeds-Dataset` and displays the closest collection photo, its parent-folder breed name, and an integer visual-similarity score. The score is not a probability that the breed name is correct.

## Requirements

- Python 3.11
- The local `Dog-Breeds-Dataset/` folder
- Network access for the first download of the pinned CLIP checkpoint, unless weights are already cached

## Install

```powershell
py -3.11 -m venv .venv311
.\.venv311\Scripts\python.exe -m pip install -e ".[dev,model]"
```

The model checkpoint is pinned by revision. Inference and reference-image matching run locally; no external image-recognition API is used.

## Validate and Build the Reference Index

```powershell
.\.venv311\Scripts\python.exe -m dog_match validate-dataset --dataset .\Dog-Breeds-Dataset
.\.venv311\Scripts\python.exe -m dog_match build-index --dataset .\Dog-Breeds-Dataset --cache-dir .\.cache\dog-match
```

The dataset is treated as read-only. Breed names come only from image parent-folder titles. The generated vector index is rebuildable and stored outside the dataset; it does not copy image files.

## Start the App

```powershell
.\.venv311\Scripts\python.exe -m dog_match serve --dataset .\Dog-Breeds-Dataset --cache-dir .\.cache\dog-match --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/`. The page is served from the same origin as its API and works without browser plugins or extensions.

## Privacy and Upload Safety

Uploaded photos are accepted as bounded multipart data, validated as readable JPEG content, processed in memory for one match, and discarded after the response. The application does not create user accounts, store personal details, save uploaded photos, retain match history, or log raw filenames/image contents. User photos are never added to the reference index.

## Similarity and Accuracy

The displayed 1-100% number is a linear display conversion of cosine similarity between normalized CLIP image vectors. It is not calibrated breed confidence. The result is the closest photo available in this project collection, not a guaranteed breed identification.

Run the 100-photo evaluation after building the full reference index:

```powershell
.\.venv311\Scripts\python.exe scripts\evaluate_matching.py --dataset .\Dog-Breeds-Dataset --cache-dir .\.cache\dog-match --sample-size 100 --seed 42
```

The initial release gate is at least 80 correct parent-folder breed labels out of 100. Do not claim this threshold is met until the evaluation report is produced.

## Tests and Type Checking

```powershell
.\.venv311\Scripts\python.exe -m pytest --cov=dog_match --cov-report=term-missing --cov-fail-under=80.1
.\.venv311\Scripts\python.exe -m mypy src\dog_match
```

Coverage must be strictly greater than 80%. Browser-flow tests use Playwright. WebKit provides a Safari-family check on Windows; verify actual Safari on a macOS test host for a release browser matrix.

## Dataset Attribution

The `Dog-Breeds-Dataset/` directory includes its own `README.md` and CC BY 4.0 `LICENSE`. Preserve both with the collection and retain attribution to the original dataset source as identified in its accompanying metadata. The presence of the FCI breed list does not by itself establish that FCI authored or licensed every photograph.
