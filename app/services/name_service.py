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
                if not self._is_duplicate(name, generated_names):
                    pronunciation = self._generate_pronunciation(name) if request.include_pronunciation else None

                    generated_names.append(GeneratedName(
                                               name=name,
                                               pronunciation=pronunciation,
                                               syllables=syllables,
                                               score=roune(score, 3),
                                               culture=request.culture.value,
                                               gender=request.gender.value if request.gender else None
                                           ))

                    self._store_name(name, request, syllables, score)

            attempts += 1

        await self.cache.set(cache_key, generated_names, ttl=3600)

        return NameGenerationResponse(
            names=generated_names,
            generation_time_ms=round((time.time() - start_time) * 1000, 2),
            parameters=request.dict()
        )

    def _generate_pronunciation(self, name: str) -> str:
        # TODO: implement IPA
        syllables = self._split_into_syllables(name)
        return '-'.join(syllables).lower()

    def _split_into_syllables(self, name: str) -> List[str]:
        # MVP Simple Rule: split on consonant-vowel boundaries
        # Placeholder until proper syllibification can be implemented
        vowels = 'aeiouy'
        syllables = []
        current = ''

        for i, char in enumerate(name.lower()):
            current += char
            if char in vowels:
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
