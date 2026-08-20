from typing import Literal

from pydantic import BaseModel, Field


class GeoJSONGeometry(BaseModel):
    type: Literal[
        "Point",
        "LineString",
        "Polygon",
        "MultiPoint",
        "MultiLineString",
        "MultiPolygon",
    ]

    coordinates: list


class NDVIToolInput(BaseModel):
    aoi: GeoJSONGeometry = Field(
        description="GeoJSON geometry representing the area of interest."
    )

    start_date: str = Field(description="Analysis start date in YYYY-MM-DD format.")

    end_date: str = Field(description="Analysis end date in YYYY-MM-DD format.")

    max_cloud_percentage: float = Field(
        default=20.0,
        ge=0.0,
        le=100.0,
        description="Maximum allowed scene-level cloud percentage.",
    )

    scale: int = Field(default=10, gt=0, description="Analysis resolution in meters.")


class LandcoverToolInput(BaseModel):
    aoi: GeoJSONGeometry = Field(
        description="GeoJSON geometry representing the area of interest."
    )

    start_date: str = Field(description="Analysis start date in YYYY-MM-DD format.")

    end_date: str = Field(description="Analysis end date in YYYY-MM-DD format.")

    scale: int = Field(default=10, gt=0, description="Analysis resolution in meters.")
