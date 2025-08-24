# app/api/v1/routes.py
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List
from app.models.schema import (
    NameGenerationRequest,
    NameGenerationResponse,
    CultureInfo,
    NameDetails
)

router = APIRouter(prefix="/names", tags=["names"])

@router.post("/generate", response_model=NameGenerationResponse)
async def generate_names(
    request: NameGenerationRequest,
    service: NameService = Depends(get_name_service)
) -> NameGenerationResponse:
    """
        Parameters:
        - Culture: The cultural style (elvish, dwarven, human) - will update human to be more specific
        - gender: masculine, feminine, neutral
        - count: number of names to generate
        - length: short, medium, long
        - include_pronunciation: IPA pronunciation
    """
    return await service.generate_names(request)

@router.get("/cultures", response_model=List[CultureInfo])
async def list_cultures(
    service: NameService = Depends(get_name_service)
) -> List[CultureInfo]:
    return await service.get_cultures()

@router.get("/validate/{name}", response_model=NameDetails)
async def validate_name(
    name: str,
    culture: Optional[str] = Query(None, description="Culture to validate against")
    service: NameService = Depends(get_name_service)
) -> NameDetails:
    # Validate and score pronunciation and quality
    return await service.validate_name(name, culture)

@router.get("/random", response_model=NameGenerationResponse)
async def get_random_name(
    culture: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    service: NameService = Depends(get_name_service)
) -> NameGenerationResponse:
    return await service.get_random_name(culture, gender)
