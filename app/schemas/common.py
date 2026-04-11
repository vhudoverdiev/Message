from datetime import datetime

from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str


class MessageOut(BaseModel):
    id: int
    dialog_id: str
    text: str
    is_read: bool
    sent_at: datetime
