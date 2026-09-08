from pydantic import BaseModel, ConfigDict


class RoutePointResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sequence_index: int
    latitude: float
    longitude: float


class RouteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    start_location: str
    end_location: str
    points: list[RoutePointResponse]
