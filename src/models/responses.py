from pydantic import BaseModel, Field
from typing import Dict, Optional

class HealthResponse(BaseModel):
    status: str
    db_connected: bool
    message: str


class UnitInfo(BaseModel):
    apartment: Optional[str]
    block: Optional[str]

class SuccessData(BaseModel):
    candidates: int
    names_with_units_info: Dict[str, UnitInfo]
    reason: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "candidates": 2,
                "names_with_units_info": {
                    "name1": {"apartment": "101", "block": "A"},
                    "name2": {"apartment": "102", "block": "B"}
                },
                "reason": "Motivo dos valores retornados"
            }
        }
    }

class SuccessResponse(BaseModel):
    status: str = "success"
    data: SuccessData


class ErrorData(BaseModel):
    message: str
    traceback: Optional[str] = None

class ErrorResponse(BaseModel):
    status: str = "error"
    data: ErrorData
