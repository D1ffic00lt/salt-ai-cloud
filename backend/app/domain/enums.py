from enum import StrEnum


class WorkspaceRole(StrEnum):
    OWNER = "owner"
    MEMBER = "member"


class RunStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"


class ArtifactKind(StrEnum):
    CHECKPOINT = "checkpoint"
    MODEL = "model"
    LOG = "log"
    MANIFEST = "manifest"
    EXPORT = "export"
    OTHER = "other"


class ArtifactStatus(StrEnum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    FAILED = "failed"
    DELETED = "deleted"


class EventLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
