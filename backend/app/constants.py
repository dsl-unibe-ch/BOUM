from enum import IntEnum

class UserRole(IntEnum):
    ADMIN = 0
    USER = 1

class VideoStatus(IntEnum):
    PENDING = 0
    SEEN = 1
    CHECKED = 2
    PROCESSING = 3
    PROCESSED = 4
    FAILED = 5