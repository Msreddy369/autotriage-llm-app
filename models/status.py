from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "waiting_approval"
    COMPLETED = "completed"
    REJECTED = "rejected"
    NOT_FOUND = "not_found"
