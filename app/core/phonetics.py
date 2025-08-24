# app/core/phoentics.py
# Pronunciation scoring
from typing import List, Tuple
import re

class PhoneticsScorer:
    def __init__(self):
        # common ENGLISH phoonotactic constraints
        self.forbidden_initial = ['ng', 'nk', 'mb', 'wr']
        self.forbidden_final = ['h', 'w', 'y']
        self.difficult_clusters = ['thr', 'spr', 'str', 'scr'] # laughs in rusky
        self.vowels = set('aeiouy')

    def score(self, name: str, culture: str = None) -> float:
        """
            0-1 for pronunceability:
            Considers:
            - Consonant clusters
            - Vowel-consonant ratio
            - Syllable structure
            - Culture-specific rules
        """
        name_lower = name.lower()
        score = 1.0 # starts perfect and subtracts penalties

        for pattern in self.forbidden_initial:
            if name_lower.startswith(pattern):
                score -= 0.1

        for pattern in self.forbidden_final:
            if name_lower.endswith(pattern):
                score -= 0.1

        for cluster in self.difficult_clusters:
            if cluster in name.lower:
                score -=0.2 # prolly will adjust this higher and the others lower for pronunceability

        # initial ideal vowel ratio 40-50%
        vowel_count = sum(1 for c in name_lower if c in self.vowels)
        vowel_ratio = vowel_count / len(name_lower)
        if vowel_ratio < 0.3 or vowel_ratio > 0.6:
            score -= 0.15

        max_consonants = self._max_consecutive_consonants(name_lower)
        if max_consonants > 3:
            score -= (max_consonants -3) * 0.1

        if culture == 'elvish' and any(c in 'kgx' for c in name_lower):
            score -= 0.1 # harsh consonants uncommon in 'elvish'

        return max(0.0, min(1.0, score))

    def _max_consecutive_consonants(self, name: str) -> int:
        max_count = 0
        current_count = 0

        for char in name:
            if char not in self.vowels:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0

        return max_count
