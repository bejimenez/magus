# Name Generator MVP Technical Specification

## Executive Summary
A self-contained Python/FastAPI service that generates pronounceable fantasy names using syllable-based patterns. SQLite stores templates and generated names for caching, while Python handles all generation logic.

## API Design Decision: REST vs GraphQL

### Recommendation: **REST for MVP, GraphQL-ready architecture**

**Why REST for MVP:**
- Simpler implementation for straightforward request/response patterns
- Name generation is primarily a single operation, not graph traversal
- Easier caching strategies with HTTP cache headers
- Lower complexity for initial development

**GraphQL would benefit in Phase 3+ when you have:**
- Complex queries like "get all names with etymology containing 'moon' from cultures that use suffix '-iel'"
- Relationship traversal (names → morphemes → meanings → related names)
- Selective field returns (just name vs full etymology data)

**Compromise Architecture:**
Design the service layer to be protocol-agnostic, making GraphQL addition straightforward later.

---

## Technology Stack

### Core Dependencies
```python
# requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
pydantic==2.5.0
python-multipart==0.0.6

# Data & Processing
pandas==2.1.3
numpy==1.26.2
weighted-levenshtein==0.2.2  # For similarity scoring

# Caching & Performance  
redis==5.0.1  # Optional, for distributed caching
python-jose[cryptography]==3.3.0  # For API keys if needed

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.1  # For API testing
faker==20.0.3  # For test data generation

# Development
python-dotenv==1.0.0
black==23.11.0
mypy==1.7.0
pre-commit==3.5.0
```

### Optional Enhancements
```python
# Consider for production
strawberry-graphql==0.211.1  # If adding GraphQL later
prometheus-client==0.19.0  # For metrics
structlog==23.2.0  # For structured logging
```

---

## Project Structure

```
name-generator/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Configuration management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py      # API endpoints
│   │   │   └── dependencies.py # Shared dependencies
│   ├── core/
│   │   ├── __init__.py
│   │   ├── generator.py       # Name generation logic
│   │   ├── phonetics.py       # Pronunciation scoring
│   │   ├── syllables.py       # Syllable patterns
│   │   └── templates.py       # Culture templates
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py        # SQLAlchemy models
│   │   ├── schemas.py         # Pydantic models
│   │   └── enums.py           # Shared enumerations
│   ├── services/
│   │   ├── __init__.py
│   │   ├── name_service.py    # Business logic layer
│   │   ├── cache_service.py   # Caching logic
│   │   └── scoring_service.py # Quality scoring
│   └── data/
│       ├── __init__.py
│       ├── cultures/           # JSON culture definitions
│       │   ├── elvish.json
│       │   ├── dwarven.json
│       │   └── human.json
│       └── phonetics.json      # Phonetic rules
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── migrations/                  # Alembic migrations
├── scripts/
│   ├── seed_database.py
│   └── validate_names.py
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## Database Schema (SQLite)

```sql
-- Culture templates
CREATE TABLE cultures (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    code TEXT NOT NULL UNIQUE,  -- 'elv', 'dwf', 'hum'
    description TEXT,
    config JSON NOT NULL,  -- Syllable patterns, rules
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Syllable patterns
CREATE TABLE syllable_patterns (
    id INTEGER PRIMARY KEY,
    culture_id INTEGER NOT NULL,
    pattern_type TEXT NOT NULL,  -- 'prefix', 'middle', 'suffix'
    pattern TEXT NOT NULL,  -- 'CV', 'CVC', 'VC'
    weight REAL DEFAULT 1.0,  -- Probability weight
    gender TEXT,  -- NULL, 'masculine', 'feminine', 'neutral'
    FOREIGN KEY (culture_id) REFERENCES cultures(id)
);

-- Generated names cache
CREATE TABLE generated_names (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    culture_id INTEGER NOT NULL,
    gender TEXT,
    pronunciation TEXT,
    syllables JSON,  -- ["Ly", "ra", "lei"]
    score REAL,
    parameters JSON,  -- Original request params
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (culture_id) REFERENCES cultures(id),
    UNIQUE(name, culture_id)
);

-- Create indexes
CREATE INDEX idx_culture_gender ON generated_names(culture_id, gender);
CREATE INDEX idx_name_score ON generated_names(score DESC);
```

---

## API Specification

### Base Configuration
```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    app_name: str = "Name Generator API"
    version: str = "1.0.0"
    api_v1_prefix: str = "/api/v1"
    
    # Database
    database_url: str = "sqlite:///./name_generator.db"
    
    # Generation settings
    max_name_length: int = 12
    min_name_length: int = 3
    default_count: int = 1
    max_count: int = 20
    
    # Caching
    cache_ttl: int = 3600  # 1 hour
    use_redis: bool = False
    redis_url: str = "redis://localhost:6379"
    
    # Performance
    max_syllables: int = 4
    min_score_threshold: float = 0.6
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
```

### API Endpoints

```python
# app/api/v1/routes.py
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List
from app.models.schemas import (
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
    Generate one or more names based on specified parameters.
    
    Parameters:
    - culture: The cultural style (elvish, dwarven, human)
    - gender: Gender association (masculine, feminine, neutral)
    - count: Number of names to generate (1-20)
    - length: Desired length (short, medium, long)
    - include_pronunciation: Include IPA pronunciation
    """
    return await service.generate_names(request)

@router.get("/cultures", response_model=List[CultureInfo])
async def list_cultures(
    service: NameService = Depends(get_name_service)
) -> List[CultureInfo]:
    """List all available naming cultures with their characteristics."""
    return await service.get_cultures()

@router.get("/validate/{name}", response_model=NameDetails)
async def validate_name(
    name: str,
    culture: Optional[str] = Query(None, description="Culture to validate against"),
    service: NameService = Depends(get_name_service)
) -> NameDetails:
    """
    Validate and score an existing name.
    Returns pronunciation and quality scores.
    """
    return await service.validate_name(name, culture)

@router.get("/random", response_model=NameGenerationResponse)
async def get_random_name(
    culture: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    service: NameService = Depends(get_name_service)
) -> NameGenerationResponse:
    """Get a single random name with optional filters."""
    return await service.get_random_name(culture, gender)
```

### Request/Response Models

```python
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
    SHORT = "short"  # 3-5 characters
    MEDIUM = "medium"  # 6-8 characters
    LONG = "long"  # 9-12 characters

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
```

---

## Core Generation Logic

```python
# app/core/generator.py
import random
from typing import List, Optional, Tuple
from app.core.syllables import SyllableGenerator
from app.core.phonetics import PhoneticsScorer
from app.models.enums import Culture, Gender, Length

class NameGenerator:
    def __init__(self, culture_templates: dict):
        self.templates = culture_templates
        self.syllable_gen = SyllableGenerator()
        self.scorer = PhoneticsScorer()
    
    def generate(
        self,
        culture: Culture,
        gender: Optional[Gender] = None,
        length: Optional[Length] = None,
        attempts: int = 100
    ) -> Tuple[str, List[str], float]:
        """
        Generate a name with syllables and score.
        Returns: (name, syllables, score)
        """
        template = self.templates[culture]
        
        for _ in range(attempts):
            syllables = self._generate_syllables(template, gender, length)
            name = ''.join(syllables)
            
            # Apply culture-specific transformations
            name = self._apply_transforms(name, template)
            
            # Score the name
            score = self.scorer.score(name, culture)
            
            if score >= 0.6:  # Minimum acceptable score
                return name.capitalize(), syllables, score
        
        # Fallback if no good name found
        return self._fallback_name(culture, gender)
    
    def _generate_syllables(
        self, 
        template: dict, 
        gender: Optional[Gender],
        length: Optional[Length]
    ) -> List[str]:
        """Generate syllables based on template patterns."""
        num_syllables = self._determine_syllable_count(length)
        patterns = template['patterns']
        
        if gender and gender in template.get('gender_patterns', {}):
            patterns = template['gender_patterns'][gender]
        
        syllables = []
        for i in range(num_syllables):
            if i == 0:
                pattern = random.choice(patterns['initial'])
            elif i == num_syllables - 1:
                pattern = random.choice(patterns['final'])
            else:
                pattern = random.choice(patterns['medial'])
            
            syllable = self.syllable_gen.generate(pattern, template)
            syllables.append(syllable)
        
        return syllables
```

```python
# app/core/syllables.py
import random
from typing import Dict, List

class SyllableGenerator:
    """Generate syllables from patterns like CV, CVC, VC."""
    
    def __init__(self):
        self.default_consonants = 'bcdfghjklmnprstvwyz'
        self.default_vowels = 'aeiou'
    
    def generate(self, pattern: str, template: Dict) -> str:
        """
        Generate a syllable from a pattern.
        C = consonant, V = vowel, N = nasal, L = liquid
        """
        consonants = template.get('consonants', self.default_consonants)
        vowels = template.get('vowels', self.default_vowels)
        nasals = template.get('nasals', 'mn')
        liquids = template.get('liquids', 'lr')
        
        result = []
        for char in pattern:
            if char == 'C':
                result.append(random.choice(consonants))
            elif char == 'V':
                result.append(random.choice(vowels))
            elif char == 'N':
                result.append(random.choice(nasals))
            elif char == 'L':
                result.append(random.choice(liquids))
            else:
                result.append(char)  # Literal character
        
        return ''.join(result)
```

---

## Culture Template Definitions

```json
// app/data/cultures/elvish.json
{
  "name": "Elvish",
  "code": "elv",
  "description": "Flowing, melodic names with soft consonants",
  "consonants": "lmnrsvwy",
  "vowels": "aeiouy",
  "liquids": "lr",
  "nasals": "mn",
  "patterns": {
    "initial": ["V", "CV", "LV"],
    "medial": ["CV", "V", "LV"],
    "final": ["V", "VC", "VL", "VN"]
  },
  "gender_patterns": {
    "feminine": {
      "initial": ["V", "LV"],
      "final": ["V", "VL"]
    },
    "masculine": {
      "initial": ["CV", "CVC"],
      "final": ["VC", "VN"]
    }
  },
  "transforms": {
    "double_l": "ll→l",
    "double_n": "nn→n"
  },
  "forbidden_sequences": ["ml", "nm", "sr"],
  "example_names": ["Lyralei", "Aelion", "Silvain", "Elowen"]
}
```

---

## Pronunciation Scoring

```python
# app/core/phonetics.py
from typing import List, Tuple
import re

class PhoneticsScorer:
    """Score names for pronounceability."""
    
    def __init__(self):
        # Common English phonotactic constraints
        self.forbidden_initial = ['ng', 'nk', 'mb', 'wr']
        self.forbidden_final = ['h', 'w', 'y']
        self.difficult_clusters = ['thr', 'spr', 'str', 'scr']
        self.vowels = set('aeiouy')
    
    def score(self, name: str, culture: str = None) -> float:
        """
        Score a name from 0-1 for pronounceability.
        Considers:
        - Consonant clusters
        - Vowel-consonant ratio
        - Syllable structure
        - Culture-specific rules
        """
        name_lower = name.lower()
        score = 1.0
        
        # Check forbidden patterns
        for pattern in self.forbidden_initial:
            if name_lower.startswith(pattern):
                score -= 0.2
        
        for pattern in self.forbidden_final:
            if name_lower.endswith(pattern):
                score -= 0.2
        
        # Check difficult clusters
        for cluster in self.difficult_clusters:
            if cluster in name_lower:
                score -= 0.1
        
        # Check vowel ratio (ideal is 40-50%)
        vowel_count = sum(1 for c in name_lower if c in self.vowels)
        vowel_ratio = vowel_count / len(name_lower)
        if vowel_ratio < 0.3 or vowel_ratio > 0.6:
            score -= 0.15
        
        # Check for too many consecutive consonants
        max_consonants = self._max_consecutive_consonants(name_lower)
        if max_consonants > 3:
            score -= (max_consonants - 3) * 0.1
        
        # Culture-specific adjustments
        if culture == 'elvish' and any(c in 'kgx' for c in name_lower):
            score -= 0.1  # Harsh consonants uncommon in elvish
        
        return max(0.0, min(1.0, score))
    
    def _max_consecutive_consonants(self, name: str) -> int:
        """Find the maximum number of consecutive consonants."""
        max_count = 0
        current_count = 0
        
        for char in name:
            if char not in self.vowels:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0
        
        return max_count
```

---

## Service Layer

```python
# app/services/name_service.py
from typing import List, Optional
import time
from sqlalchemy.orm import Session
from app.core.generator import NameGenerator
from app.models.schemas import (
    NameGenerationRequest,
    NameGenerationResponse,
    GeneratedName
)
from app.models.database import Culture as DBCulture

class NameService:
    def __init__(self, db: Session, cache_service: CacheService):
        self.db = db
        self.cache = cache_service
        self.generator = NameGenerator(self._load_templates())
    
    async def generate_names(
        self, 
        request: NameGenerationRequest
    ) -> NameGenerationResponse:
        """Generate names based on request parameters."""
        start_time = time.time()
        
        # Check cache for similar requests
        cache_key = self._generate_cache_key(request)
        cached = await self.cache.get(cache_key)
        if cached and len(cached) >= request.count:
            return self._format_response(
                cached[:request.count], 
                request, 
                time.time() - start_time
            )
        
        generated_names = []
        attempts = 0
        max_attempts = request.count * 10
        
        while len(generated_names) < request.count and attempts < max_attempts:
            name, syllables, score = self.generator.generate(
                culture=request.culture,
                gender=request.gender,
                length=request.length
            )
            
            if score >= request.min_score:
                # Check uniqueness
                if not self._is_duplicate(name, generated_names):
                    pronunciation = self._generate_pronunciation(name) if request.include_pronunciation else None
                    
                    generated_names.append(GeneratedName(
                        name=name,
                        pronunciation=pronunciation,
                        syllables=syllables,
                        score=round(score, 3),
                        culture=request.culture.value,
                        gender=request.gender.value if request.gender else None
                    ))
                    
                    # Store in database
                    self._store_name(name, request, syllables, score)
            
            attempts += 1
        
        # Cache the results
        await self.cache.set(cache_key, generated_names, ttl=3600)
        
        return NameGenerationResponse(
            names=generated_names,
            generation_time_ms=round((time.time() - start_time) * 1000, 2),
            parameters=request.dict()
        )
    
    def _generate_pronunciation(self, name: str) -> str:
        """Generate simple pronunciation guide."""
        # MVP: Simple syllable-based pronunciation
        # Phase 2 will use IPA
        syllables = self._split_into_syllables(name)
        return '-'.join(syllables).lower()
    
    def _split_into_syllables(self, name: str) -> List[str]:
        """Basic syllable splitting for MVP."""
        # Simple rule: split on consonant-vowel boundaries
        # This is a placeholder - Phase 2 will have proper syllabification
        vowels = 'aeiouy'
        syllables = []
        current = ''
        
        for i, char in enumerate(name.lower()):
            current += char
            if char in vowels:
                # Look ahead for consonant-vowel boundary
                if i + 1 < len(name) and name[i + 1] not in vowels:
                    if i + 2 < len(name) and name[i + 2] in vowels:
                        current += name[i + 1]
                        syllables.append(current)
                        current = ''
        
        if current:
            if syllables:
                syllables[-1] += current
            else:
                syllables.append(current)
        
        return syllables
```

---

## Testing Strategy

```python
# tests/unit/test_generator.py
import pytest
from app.core.generator import NameGenerator
from app.core.phonetics import PhoneticsScorer

class TestNameGenerator:
    @pytest.fixture
    def generator(self):
        templates = {
            'elvish': {
                'consonants': 'lmnrsvy',
                'vowels': 'aeiou',
                'patterns': {
                    'initial': ['CV', 'V'],
                    'medial': ['CV', 'V'],
                    'final': ['V', 'VC']
                }
            }
        }
        return NameGenerator(templates)
    
    def test_generates_valid_name(self, generator):
        name, syllables, score = generator.generate('elvish')
        assert len(name) >= 3
        assert 0.0 <= score <= 1.0
        assert len(syllables) >= 1
    
    def test_respects_length_constraint(self, generator):
        name, _, _ = generator.generate('elvish', length='short')
        assert len(name) <= 5
        
        name, _, _ = generator.generate('elvish', length='long')
        assert len(name) >= 9

class TestPhoneticsScorer:
    @pytest.fixture
    def scorer(self):
        return PhoneticsScorer()
    
    def test_scores_pronounceable_names_high(self, scorer):
        assert scorer.score('Lyra') > 0.8
        assert scorer.score('Elena') > 0.8
    
    def test_scores_difficult_names_low(self, scorer):
        assert scorer.score('Xkrth') < 0.5
        assert scorer.score('Zzzng') < 0.5
```

---

## Deployment Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/name_generator.db
      - PYTHONPATH=/app
    volumes:
      - ./data:/app/data
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python scripts/seed_database.py

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Performance Considerations

### Caching Strategy
1. **In-memory cache**: LRU cache for culture templates
2. **SQLite cache**: Store successful generations
3. **Optional Redis**: For distributed deployments

### Optimization Targets
- Response time: < 50ms for single name
- Batch generation: < 200ms for 20 names
- Memory usage: < 100MB baseline
- SQLite queries: Indexed lookups only

### Monitoring Points
- Generation success rate (% above min_score)
- Cache hit ratio
- Average response time per culture
- Unique name generation rate

---

## Next Steps After MVP

1. **Week 4**: Add IPA pronunciation generation
2. **Week 5**: Implement Markov chain phoneme transitions
3. **Week 6**: Add phonotactic constraint validation
4. **Week 7**: Begin morphological component research

This MVP provides a solid foundation that can generate names like "Lyralei" or "Thormund" with basic quality assurance, while keeping the architecture flexible for your planned enhancements.