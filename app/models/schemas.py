# app/models/schemas.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from enum import Enum

class Gender(str, Enum):
    MASCULINE = "masculine"
    FEMININE = "feminine"
    NEUTRAL = "neutral"

class Culture(str, Enum):
    ELVISH = "elvish"
    DWARVEN = "dwarven"
    HUMAN = "human"

class Length(str, Enum):
    SHORT = "short" # 3-5 chars
    MEDIUM = "medium" # 6-10 chars
    LONG = "long" # 11-15 chars

class NameGenerationRequest(BaseModel):
    culture: Culture
    gender: Optional[Gender] = None
    count: int = Field(default=1, ge=1, le=20)
    length: Optional[Length] = None
    include_pronunciation: bool = True
    min_score: float = Field(default=0.6, ge=0.0, le=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "culture": "elvish",
                "gender": "feminine",
                "count": 5,
                "length": "medium",
                "include_pronunciation": True
            }
        }

class GeneratedName(BaseModel):
    name: str
    pronunciation: Optional[str] = None
    syllables: List[str]
    score: float = Field(ge=0.0, le=1.0)
    culture: str
    gender: Optional[str] = None

class NameGenerationResponse(BaseModel):
    names: List[GeneratedName]
    generation_time_ms: float
    parameters: dict

class CultureInfo(BaseModel):
    code: str
    name: str
    description: str
    typical_length: str
    common_sounds: List[str]
    example_names: List[str]
