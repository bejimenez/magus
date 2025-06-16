# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import random
import json
from pathlib import Path

# Initialize FastAPI app
app = FastAPI(
    title="AI Name Generator MVP",
    description="A simple API that generates random names from predefined lists.",
    version="1.0.0",
)

# Pydantic models for request/response
class NameRequest(BaseModel):
    culture: Optional[str] = "generic"
    gender: Optional[str] = None
    count: Optional[int] = 1

class NameResponse(BaseModel):
    name: str
    culture: str
    gender: Optional[str] = None

class NamesResponse(BaseModel):
    names: List[NameResponse]
    total_count: int

# hardcoded names for different cultures
# in a real application, these would be loaded from a database or external service
NAMES_DB = {
    "generic": {
        "male": [
            "Alexander", "Benjamin", "Christopher", "Daniel", "Edward",
            "Frederick", "Gabriel", "Henry", "Isaac", "James"
        ],
        "female": [
            "Alexandra", "Beatrice", "Catherine", "Diana", "Eleanor",
            "Francesca", "Gabrielle", "Helena", "Isabella", "Josephine"
        ],
        "unisex": [
            "Alex", "Blake", "Cameron", "Dakota", "Emery",
            "Finley", "Gray", "Hayden", "Indigo", "Jordan"
        ]
    },
    "elvish": {
        "male": [
            "Aelindra", "Celeborn", "Elrond", "Faelar", "Galion",
            "Haldir", "Ivellios", "Legolas", "Mindartis", "Naal"
        ],
        "female": [
            "Arwen", "Celebrian", "Elaria", "Galadriel", "Idril",
            "Nimrodel", "Tauriel", "Elenwë", "Aredhel", "Finduilas"
        ]
    },
    "norse": {
        "male": [
            "Bjorn", "Erik", "Gunnar", "Harald", "Ivar",
            "Magnus", "Olaf", "Ragnar", "Sigurd", "Thor"
        ],
        "female": [
            "Astrid", "Brynhild", "Freydis", "Gudrun", "Helga",
            "Ingrid", "Ragnhild", "Sigrid", "Thora", "Valdis"
        ]
    }
}

class NameGenerator:
    """Simple name generator that selects from pre-populated lists."""
    def __init__(self, names_db: dict):
        self.names_db = names_db

    def get_available_cultures(self) -> List[str]:
        """Return a list of available cultures."""
        return list(self.names_db.keys())
    
    def get_available_genders(self, culture: str) -> List[str]:
        """Return available genders for a given culture."""
        if culture not in self.names_db:
            return []
        return list(self.names_db[culture].keys())
    
    def generate_name(self, culture: str = "generic", gender: Optional[str] = None) -> NameResponse:
        """Generate a single random name"""
        # validate culture
        if culture not in self.names_db:
            available_cultures = self.get_available_cultures()
            raise ValueError(f"Culture '{culture}' not found. Available cultures: {available_cultures}")
        
        culture_data = self.names_db[culture]

        # if no gender specified, choose one randomly
        if gender is None:
            available_genders = list(culture_data.keys())
            gender = random.choice(available_genders)

        # validate gender for the culture
        if gender not in culture_data:
            available_genders = list(culture_data.keys())
            raise ValueError(f"Gender '{gender}' not available for culture '{culture}'. Available: {available_genders}")
        
        # Select a random name from the appropriate list
        name_list = culture_data[gender]
        selected_name = random.choice(name_list)

        return NameResponse(
            name=selected_name,
            culture=culture,
            gender=gender
        )
    
    def generate_multiple_names(self, culture: str = "generic", gender: Optional[str] = None, count: int = 1) -> List[NameResponse]:
        """Generate multiple random names"""
        if count < 1 or count > 50: # limit to prevent abuse
            raise ValueError("Count must be between 1 and 50.")
        
        names = []
        for _ in range(count):
            names.append(self.generate_name(culture, gender))
        return names
    
# Initialize the name generator with the hardcoded names
name_generator = NameGenerator(NAMES_DB)

# API Routes
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Magus: The AI Name Generator MVP",
        "version": "1.0.0",
        "endpoints": {
            "generate": "/generate - Generate random names",
            "cultures": "/cultures - List available cultures",
            "health": "/health - Check API health",
        }
    }

@app.post("/generate", response_model=NamesResponse)
async def generate_names(request: NameRequest):
    """Generate one or more random names based on criteria."""
    try:
        names = name_generator.generate_multiple_names(
            culture=request.culture or "generic",
            gender=request.gender,
            count=request.count or 1
        )

        return NamesResponse(
            names=names,
            total_count=len(names)
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    
@app.get("/cultures")
async def get_cultures():
    """List all available cultures and their supported genders."""
    cultures_info = {}
    for culture in name_generator.get_available_cultures():
        cultures_info[culture] = {
            "genders": name_generator.get_available_genders(culture),
            "total_names": sum(len(names) for names in NAMES_DB[culture].values())
        }
    
    return {
        "available_cultures": cultures_info,
        "total_cultures": len(cultures_info)
    }

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "total_names": sum(
            len(names)
            for culture in NAMES_DB.values()
            for names in culture.values()
        )
    }

# Run the app with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)