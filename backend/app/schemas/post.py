import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InstagramPostResponse(BaseModel):
    id: uuid.UUID
    stop_id: str
    instagram_id: str
    shortcode: str
    media_url: str
    caption: str
    timestamp: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubstackPostResponse(BaseModel):
    id: uuid.UUID
    stop_id: str | None
    substack_id: str
    title: str
    subtitle: str | None
    body: str
    published_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
