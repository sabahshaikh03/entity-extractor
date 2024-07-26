from pydantic import BaseModel
from typing import Any, Optional

class ResponseEntityDTO(BaseModel):
    message: str
    result: Optional[Any] = None
    total_count: int

    class Config:
        # This will allow field names to be recognized with snake_case
        alias_generator = lambda string: string.lower() if string != "total_count" else "totalCount"
        populate_by_name = True
