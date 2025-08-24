# app/core/syllables.py
import random
from typing import Dict, List

class SyllableGenerator:
    """This is the default syllable generator pattern config
    CV, CVC, VC.
    
    Later implementations for other cultures (slavic) will include
    other patterns like CCV or NCCV that are less pronunciable for
    native speakers of Romance languages
    """

    def __init__(self):
        self.default_consonants = 'bcdfghjklmnprstvwyz'
        self.default_vowels = 'aeiouy'

    def generate(self, pattern: str, template: Dict) -> str:
        # C = Consonant, V = vowel, N = nasal, L = liquid
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
                result.append(char) # literal character or the tvordiyznak/myakiznak adjusters

        return ''.join(result)
