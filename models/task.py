from pydantic import BaseModel

class TaskRequest(BaseModel):
    request: str
    require_approval: bool
