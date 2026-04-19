from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Artifact
from app.schemas.artifact import (
    ArtifactComplete,
    ArtifactCreate,
    ArtifactDownloadRead,
    ArtifactRead,
)
from app.services.artifact_service import ArtifactService

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
) -> Artifact:
    service = ArtifactService(db)

    try:
        return service.create_artifact(run_id=run_id, data=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/runs/{run_id}/artifacts", response_model=list[ArtifactRead])
def list_run_artifacts(
        run_id: UUID,
        db: Session = Depends(get_db),
) -> list[Artifact]:
    service = ArtifactService(db)

    try:
        return service.list_run_artifacts(run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/artifacts/{artifact_id}", response_model=ArtifactRead)
def get_artifact(
        artifact_id: UUID,
        db: Session = Depends(get_db),
) -> Artifact:
    service = ArtifactService(db)

    try:
        return service.get_artifact(artifact_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/artifacts/{artifact_id}/complete", response_model=ArtifactRead)
def complete_artifact(
        artifact_id: UUID,
        payload: ArtifactComplete,
        db: Session = Depends(get_db),
) -> Artifact:
    service = ArtifactService(db)

    try:
        return service.complete_artifact(artifact_id=artifact_id, data=payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/artifacts/{artifact_id}/download", response_model=ArtifactDownloadRead)
def get_artifact_download_reference(
        artifact_id: UUID,
        db: Session = Depends(get_db),
) -> ArtifactDownloadRead:
    service = ArtifactService(db)

    try:
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
