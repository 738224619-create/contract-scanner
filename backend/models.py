from pydantic import BaseModel, Field
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class RiskItem(BaseModel):
    clause: str
    risk_level: RiskLevel
    explanation: str
    suggestion: str
    confidence: int = Field(default=50, ge=0, le=100)

class AnalysisResult(BaseModel):
    filename: str
    risks: list[RiskItem]
    summary: str
