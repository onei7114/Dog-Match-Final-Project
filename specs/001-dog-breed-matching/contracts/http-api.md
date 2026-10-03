# HTTP API Contract

The static page and JSON API are served from the same origin by FastAPI. All response bodies use UTF-8 JSON unless a route returns a JPEG image. The API does not persist uploaded photos or match history.

## `GET /api/v1/health`

Readiness for local diagnostics. This route does not expose filesystem paths.

**200 response**

```json
{
  "status": "ready",
  "breed_count": 356,
  "reference_image_count": 12230
}
```

If the service is running but its dataset/index is not ready, return `503` with the standard error body and do not report `ready`.

## `POST /api/v1/matches`

Accept one photo as `multipart/form-data` in field `file`. Supported content is a valid JPG/JPEG image, up to 10 MiB and 40 megapixels by default. The server validates decoded content rather than trusting the supplied filename or content type.

**200 response**

```json
{
  "breed_name": "border collie dog",
  "similarity_percent": 87,
  "reference_image_url": "/api/v1/reference-images/7c831dbd7b475d32",
  "disclaimer": "This is the closest visual match in the project photo collection, not a guaranteed breed identification."
}
```

`similarity_percent` is an integer from 1 through 100 and represents normalized visual similarity only. The response contains no server filesystem path and no copy of the uploaded photo.

**Errors**

| Status | Code | Meaning |
|-------:|------|---------|
| 400 | `missing_file` | No `file` part was submitted. |
| 413 | `upload_too_large` | The upload exceeds the configured byte limit. |
| 415 | `invalid_jpeg` | The upload is unsupported, corrupt, or not a decodable JPG/JPEG. |
| 503 | `index_unavailable` | The dataset or compatible index is unavailable. |
| 500 | `match_failed` | Matching failed unexpectedly; do not return a partial result. |

Error body:

```json
{
  "error": {
    "code": "invalid_jpeg",
    "message": "Choose a readable JPG or JPEG photo and try again."
  }
}
```

Error messages are user-safe; detailed exception data stays in server logs. The browser displays a recoverable message and does not retain a previous result as though it belonged to the failed upload.

## `GET /api/v1/reference-images/{reference_id}`

Return a JPEG only if `reference_id` resolves to an image in the validated index manifest. Never concatenate the supplied ID into a filesystem path.

- `200 image/jpeg`: selected reference photo.
- `404`: unknown ID or non-reference path.
- `503`: index unavailable.

## Static Page

`GET /` returns the standalone HTML page; static CSS and JavaScript are served from the same origin. The page shell must not download the full dataset or embedding index. It loads only the matched reference image after a successful response.
