"""FastAPI application factory and health route."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from dog_match.config import Settings
from dog_match.encoder import ClipImageEncoder
from dog_match.index import IndexUnavailableError, ReferenceIndex
from dog_match.matcher import find_closest_reference
from dog_match.schemas import ErrorDetail, ErrorResponse, HealthResponse, MatchResponse
from dog_match.upload_validation import (
    MissingUploadError,
    UploadTooLargeError,
    UploadValidationError,
    read_validated_jpeg,
)

logger = logging.getLogger(__name__)
DISCLAIMER = (
    "This is the closest visual match in the project photo collection, "
    "not a guaranteed breed identification."
)


def _error(code: str, message: str, http_status: int) -> JSONResponse:
    body = ErrorResponse(error=ErrorDetail(code=code, message=message))
    return JSONResponse(status_code=http_status, content=body.model_dump())


def create_app(
    settings: Settings | None = None,
    search_index: ReferenceIndex | None = None,
    encoder: ClipImageEncoder | None = None,
) -> FastAPI:
    """Create an application instance with isolated settings and runtime state."""
    app = FastAPI(title="Dog Match", version="0.1.0")
    app.state.settings = settings or Settings.from_environment()
    app.state.search_index = search_index
    app.state.image_encoder = encoder
    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def home() -> FileResponse:
        return FileResponse(static_dir / "index.html", media_type="text/html")

    @app.get("/api/v1/health")
    async def health() -> JSONResponse:
        search_index = app.state.search_index
        if search_index is None:
            return _error(
                "index_unavailable",
                "The reference collection is not ready. Run the index build command and restart the app.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        response = HealthResponse(
            status="ready",
            breed_count=search_index.breed_count,
            reference_image_count=search_index.image_count,
        )
        return JSONResponse(
            content=response.model_dump()
        )

    @app.post("/api/v1/matches", response_model=MatchResponse)
    async def create_match(request: Request) -> JSONResponse:
        current_index: ReferenceIndex | None = app.state.search_index
        current_encoder: ClipImageEncoder | None = app.state.image_encoder
        if current_index is None or current_encoder is None:
            return _error(
                "index_unavailable",
                "The reference collection is not ready. Run the index build command and restart the app.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        try:
            image = await read_validated_jpeg(
                request,
                max_upload_bytes=app.state.settings.max_upload_bytes,
                max_image_pixels=app.state.settings.max_image_pixels,
            )
            try:
                vector = current_encoder.encode([image])[0]
            finally:
                image.close()
            match = find_closest_reference(current_index, vector)
            response = MatchResponse(
                breed_name=match.breed_name,
                similarity_percent=match.similarity_percent,
                reference_image_url=f"/api/v1/reference-images/{match.reference_id}",
                disclaimer=DISCLAIMER,
            )
            return JSONResponse(content=response.model_dump())
        except MissingUploadError as exc:
            return _error("missing_file", str(exc), status.HTTP_400_BAD_REQUEST)
        except UploadTooLargeError as exc:
            return _error("upload_too_large", str(exc), status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        except UploadValidationError:
            return _error(
                "invalid_jpeg",
                "Choose a readable JPG or JPEG photo and try again.",
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )
        except IndexUnavailableError:
            return _error(
                "index_unavailable",
                "The reference collection is not ready. Rebuild the index and try again.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception:
            logger.exception("Unexpected image-match failure")
            return _error(
                "match_failed",
                "The photo could not be matched right now. Please try again.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @app.get("/api/v1/reference-images/{reference_id}")
    async def get_reference_image(reference_id: str) -> Response:
        current_index: ReferenceIndex | None = app.state.search_index
        if current_index is None:
            return _error(
                "index_unavailable",
                "The reference collection is not ready.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        record = next(
            (image for image in current_index.manifest.images if image.reference_id == reference_id),
            None,
        )
        if record is None:
            return _error("not_found", "The reference photo was not found.", status.HTTP_404_NOT_FOUND)
        try:
            root: Path = app.state.settings.dataset_root.resolve(strict=True)
            image_path = (root / record.relative_path).resolve(strict=True)
            image_path.relative_to(root)
        except ValueError:
            return _error("not_found", "The reference photo was not found.", status.HTTP_404_NOT_FOUND)
        except OSError:
            return _error(
                "index_unavailable",
                "The reference collection changed. Rebuild the index and try again.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        if not image_path.is_file():
            return _error("not_found", "The reference photo was not found.", status.HTTP_404_NOT_FOUND)
        return FileResponse(image_path, media_type="image/jpeg")

    return app


app = create_app()
