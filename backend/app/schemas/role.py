from datetime import datetime
from typing import Optional

from app.schemas.common import ORMModel


class RoleResponse(ORMModel):
    id: int
    name: str
    description: Optional[str] = None
    is_system: bool
    created_at: Optional[datetime] = None
