# Data Model: Dog Breed Matching

## Dataset Folder

The folder structure is the authoritative breed label source:

```text
Dog-Breeds-Dataset/
└── <breed folder title>/
    └── <reference image>.jpg
```

Only readable JPG/JPEG images under this root are eligible references. The immediate parent folder title is returned as the breed name. `FCI Breeds.csv` and remote URLs are not used to assign labels or find images.

## Breed Photo Record

| Field | Type | Rule |
|------|------|------|
| `reference_id` | string | Stable opaque identifier derived from the relative path; used by the image route, not a filesystem path. |
| `relative_path` | string | Path relative to the configured dataset root; never accepted from the browser. |
| `breed_name` | string | Immediate parent folder title, preserved for display. |
| `file_size` | integer | Bytes; used for inventory change detection. |
| `modified_ns` | integer | File modification time; used for inventory change detection. |
| `embedding` | numeric vector | Normalized CLIP image feature used only for similarity comparison. |

## Search Index Manifest

The generated index consists of a manifest and an embedding matrix aligned by row. The manifest records its format version, model identifier and revision, image-preprocessing version, dataset root-relative inventory, and each row's reference ID, relative path, breed name, size, and modification time. The matrix contains one normalized vector for each manifest record. A mismatch between the manifest and the runtime model, preprocessing, or image inventory makes the index invalid and requires a CLI rebuild.

The index is derived data and can be deleted and recreated. It is stored outside the read-only source dataset and is not committed as a second image store.

## Uploaded Photo

A request-scoped JPG/JPEG file that is size-limited, decoded, checked for valid image content, converted to RGB, and processed in memory. The original filename is untrusted and is not used as a path. The upload is not persisted after the response.

## Breed Match Result

| Field | Type | Rule |
|------|------|------|
| `breed_name` | string | Folder title belonging to the selected reference photo. |
| `similarity_percent` | integer | Clamped integer from 1 through 100, calculated from normalized cosine similarity; a display score, not a breed probability. |
| `reference_image_url` | string | Same-origin route containing the opaque reference ID. |
| `disclaimer` | string | States this is the closest visual match in the project collection, not guaranteed breed identification. |

The result is returned to the requesting browser and is not stored as a user record.

## Lifecycle

1. CLI scans the configured dataset and reports unreadable files and folders without changing source files.
2. CLI batch-encodes readable references and atomically writes a new versioned index.
3. Service startup validates and loads the index; invalid or missing index prevents readiness and gives rebuild guidance.
4. A match request validates and encodes one upload, compares it to indexed vectors, and returns the highest-scoring reference.
5. The browser requests that reference image by opaque ID. No upload or match history is retained.
