from enum import UNIQUE, StrEnum, verify


@verify(UNIQUE)
class PredictionRate(StrEnum):
    UNDETERMINED = "undetermined"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@verify(UNIQUE)
class ResourceStatus(StrEnum):
    CHECK = "check"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    PREDICTING = "predicting"
    CHECKED = "checked"
    DECLINED = "declined"
    DELETED = "deleted"


@verify(UNIQUE)
class ResourceType(StrEnum):
    URL = "url"
    TEXT = "text"
    FILE = "file"
    VIDEO = "video"
    IMAGE = "image"


@verify(UNIQUE)
class UserType(StrEnum):
    CUSTOMER = "customer"
    MODERATOR = "moderator"
    ADMIN = "admin"


@verify(UNIQUE)
class UserStatus(StrEnum):
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"


@verify(UNIQUE)
@verify(UNIQUE)
class TaskStatus(StrEnum):
    CHECK = "check"
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    PREDICTING = "predicting"
    CHECKED = "checked"
    DECLINED = "declined"
    DELETED = "deleted"


@verify(UNIQUE)
class TaskNotificationResponse(StrEnum):
    RECEIVED = "received"
