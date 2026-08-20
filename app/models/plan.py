from pydantic import BaseModel, Field


class AnalysisStep(BaseModel):
    tool: str = Field(description="Name of the analysis tool to execute.")

    reason: str = Field(description="Why this analysis is needed.")


class AnalysisPlan(BaseModel):
    objective: str = Field(description="The overall objective of the investigation.")

    analyses: list[AnalysisStep] = Field(
        min_length=1, description="Ordered analysis steps."
    )
