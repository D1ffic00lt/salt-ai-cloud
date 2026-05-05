from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import ensure_token_workspace, get_current_api_token, get_db, require_scope
from app.db.models import Artifact
from app.db.models.api_token import ApiToken
from app.schemas.artifact import (
    ArtifactComplete,
    ArtifactCreate,
    ArtifactDownloadRead,
    ArtifactRead,
)
from app.services.artifact_service import ArtifactService
from app.services.run_service import RunService

router = APIRouter()


@router.post(
    "/runs/{run_id}/artifacts",
    response_model=ArtifactRead,
    status_code=status.HTTP_201_CREATED,
)
def create_artifact(
        run_id: UUID,
        payload: ArtifactCreate,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> Artifact:
    run_service = RunService(db)
    artifact_service = ArtifactService(db)

    try:
        run = run_service.get_run(run_id)
        ensure_token_workspace(token, run.workspace_id)
        require_scope(token, "artifacts:write")

        return artifact_service.create_artifact(run_id=run_id, data=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/runs/{run_id}/artifacts", response_model=list[ArtifactRead])
def list_run_artifacts(
        run_id: UUID,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> list[Artifact]:
    run_service = RunService(db)
    artifact_service = ArtifactService(db)

    try:
        run = run_service.get_run(run_id)
        ensure_token_workspace(token, run.workspace_id)
        require_scope(token, "artifacts:read")

        return artifact_service.list_run_artifacts(run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/artifacts/{artifact_id}", response_model=ArtifactRead)
def get_artifact(
        artifact_id: UUID,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> Artifact:
    service = ArtifactService(db)

    try:
        artifact = service.get_artifact(artifact_id)
        ensure_token_workspace(token, artifact.workspace_id)
        require_scope(token, "artifacts:read")

        return artifact
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/artifacts/{artifact_id}/complete", response_model=ArtifactRead)
def complete_artifact(
        artifact_id: UUID,
        payload: ArtifactComplete,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> Artifact:
    service = ArtifactService(db)

    try:
        artifact = service.get_artifact(artifact_id)
        ensure_token_workspace(token, artifact.workspace_id)
        require_scope(token, "artifacts:write")

        return service.complete_artifact(artifact_id=artifact_id, data=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/artifacts/{artifact_id}/upload", response_model=ArtifactRead)
def upload_artifact(
        artifact_id: UUID,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> Artifact:
    service = ArtifactService(db)

    try:
        artifact = service.get_artifact(artifact_id)
        ensure_token_workspace(token, artifact.workspace_id)
        require_scope(token, "artifacts:write")

        return service.upload_artifact_file(artifact_id=artifact_id, file=file)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/artifacts/{artifact_id}/download", response_model=ArtifactDownloadRead)
def get_artifact_download_reference(
        artifact_id: UUID,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> ArtifactDownloadRead:
    service = ArtifactService(db)

    try:
        artifact = service.get_artifact(artifact_id)
        ensure_token_workspace(token, artifact.workspace_id)
        require_scope(token, "artifacts:read")

        artifact, download_url = service.get_download_reference(artifact_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return ArtifactDownloadRead(
        artifact_id=artifact.id,
        storage_uri=artifact.storage_uri,
        download_url=download_url,
    )


@router.get("/artifacts/{artifact_id}/content")
def get_artifact_content(
        artifact_id: UUID,
        db: Session = Depends(get_db),
        token: ApiToken = Depends(get_current_api_token),
) -> FileResponse:
    service = ArtifactService(db)

    try:
        artifact = service.get_artifact(artifact_id)
        ensure_token_workspace(token, artifact.workspace_id)
        require_scope(token, "artifacts:read")

        artifact, path = service.get_content_path(artifact_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return FileResponse(
        path=path,
        media_type=artifact.content_type or "application/octet-stream",
        filename=artifact.name,
    )
