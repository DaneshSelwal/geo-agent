from typing import Any

from pydantic import BaseModel, Field


class DataQuality(BaseModel):
    """
    Information describing the quality/amount of source data
    used by an analysis.
    """

    source_image_count: int = Field(ge=0)
    usable_image_count: int = Field(ge=0)
    valid_coverage: float = Field(ge=0.0, le=1.0)


class Methodology(BaseModel):
    """
    Describes how the analysis was performed.
    """

    dataset: str
    resolution_m: int
    composite_method: str
    cloud_masking: str
    index: str


class AnalysisResult(BaseModel):
    """
    Standard output contract for every GIS analysis tool.
    """

    analysis_type: str

    findings: dict[str, Any]

    data_quality: DataQuality

    methodology: Methodology

    limitations: list[str] = Field(default_factory=list)

    visualizations: dict[str, Any] = Field(default_factory=dict)