from app.schemas.post import InstagramPostResponse, SubstackPostResponse
from app.schemas.stop import StopResponse
from app.schemas.trip import TripBase, TripCreate, TripUpdate, TripResponse, TripDetailResponse

# Resolve forward references that cross schema modules
StopResponse.model_rebuild()
TripDetailResponse.model_rebuild()

__all__ = [
    "InstagramPostResponse",
    "SubstackPostResponse",
    "StopResponse",
    "TripBase",
    "TripCreate",
    "TripUpdate",
    "TripResponse",
    "TripDetailResponse",
]
