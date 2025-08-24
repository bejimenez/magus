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
        # generate a name and return name, syllable, score
        template = self.templates[culture]

        for _ in range(attempts):
            syllables = self._generate_syllables(template, gender, length)
            name = ''.join(syllables)

            # apply culture specific transformations
            name = self._apply_transforms(name, template)

            score = self.scorer.score(name, culture)

            if score >= 0.6:
                return name.capitalize(), syllables, score

        return self._fallback_name(culture, gender)

    def _generate_syllables(
        self,
        template: dict,
        gender: Optional[Gender],
        length: Optional[Length]
    ) -> List[str]:

        num_syllables = self._determine_syllable_count(length)
        patterns = template['patterns']

        if gender and gender in template.get('gender_patterns', {}):
            patterns = template['gender_patterns'][gender]

        syllables = []
        for i in range(num_syllables):
            if i == 0:
                pattern = random.choice(patterns['initial'])
            elif i == num_syllables -1:
                pattern = random.choice(patterns['final'])
            else:
                pattern = random.choice(patterns['medial'])

            syllable = self.syllable_gen.generate(pattern, template)
            syllables.append(syllable)

        return syllables
