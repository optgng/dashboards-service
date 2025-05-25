from pydantic import BaseModel
from typing import Optional

class Dashboard(BaseModel):
    id: Optional[int] = None
    title: str
    data: dict

    class Config:
        orm_mode = True