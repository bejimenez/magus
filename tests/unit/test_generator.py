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
