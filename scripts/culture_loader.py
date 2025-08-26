# service to load culture definitions from JSON files at startup

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import lru_cache

logger = logging.getLogger(__name__)

class CultureLoader:
    def __init__(self, culture_dir: Optional[Path] = None):
        if culture_dir is None:
            self.culture_dir = Path(__file__).parent.parent / "data"/ "cultures"
        else:
            self.culture_dir = Path(culture_dir)

        self._cultures: Dict[str, Dict] = {}

        if not self.culture_dir.exists():
            logger.warning(f"Culture directory {self.culture_dir} does not exist.")
            self.culture_dir.mkdir(parents=True, exist_ok=True)
    
    def load_all_cultures(self) -> Dict[str, Dict]:
        logger.info(f"Loading cultures from {self.culture_dir}")

        culture_files = list(self.culture_dir.glob("*.json"))

        if not culture_files:
            logger.warning(f"No culture files found in {self.culture_dir}")
            return {}
        
        for filepath in culture_files:
            try:
                culture_data = self._load_culture_file(filepath)
                if self._validate_culture(culture_data):
                    code = culture_data["code"]
                    self._cultures[code] = culture_data
                    logger.info(f"Loaded culture: {code}")
                else:
                    logger.error(f"Invalid culture data in {filepath}")
            except Exception as e:
                logger.error(f"Error loading culture from {filepath}: {e}")

        logger.info(f"Total cultures loaded: {len(self._cultures)}")
        return self._cultures
    
    def _load_culture_file(self, filepath: Path) -> Dict:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
        
    def _validate_culture(self, culture_data: Dict) -> bool:
        required_fields = ["name", "code", "description", "phonemes", "syllable_patterns"]

        for field in required_fields:
            if field not in culture_data:
                logger.error(f"Missing required field '{field}' in culture data")
                return False
            
        if not isinstance(culture_data.get("phonemes"), dict):
            logger.error("Field 'phonemes' must be a dictionary")
            return False
        
        required_phonemes = ["consonants", "vowels"]
        for phoneme in required_phonemes:
            if phoneme not in culture_data["phonemes"]:
                logger.error(f"Culture phonemes missing: {phoneme}")
                return False
        
        if not isinstance(culture_data.get("syllable_patterns"),dict):
            logger.error("Field 'syllable_patterns' must be a dictionary")
            return False
        
        required_positions = ["initial", "medial", "final"]
        for position in required_positions:
            if position not in culture_data["syllable_patterns"]:
                logger.error(f"Culture syllable patterns missing: {position}")
                return False
            
            patterns = culture_data["syllable_patterns"][position]
            if not isinstance(patterns, list):
                logger.error(f"Syllable patterns for '{position}' must be a list")
                return False
            
            for pattern in patterns:
                if not isinstance(pattern, dict) or "pattern" not in pattern:
                    logger.error(f"Invalid pattern structure in {position}")
                    return False

        return True
    
    def get_culture(self, code: str) -> Optional[Dict]:
        """
        Get a specific culture by its code.
        
        Args:
            code: Culture code (e.g., 'elv', 'dwf', 'hum')
            
        Returns:
            Culture data dictionary or None if not found
        """
        return self._cultures.get(code)
    
    def get_culture_names(self) -> List[str]:
        """
        Get list of all loaded culture names.
        
        Returns:
            List of culture names
        """
        return [culture["name"] for culture in self._cultures.values()]
    
    def get_culture_codes(self) -> List[str]:
        """
        Get list of all loaded culture codes.
        
        Returns:
            List of culture codes
        """
        return list(self._cultures.keys())
    
    def get_phonemes(self, code: str) -> Optional[Dict[str, str]]:
        """
        Get phoneme sets for a specific culture.
        
        Args:
            code: Culture code
            
        Returns:
            Dictionary of phoneme sets or None
        """
        culture = self.get_culture(code)
        return culture.get("phonemes") if culture else None
    
    def get_syllable_patterns(self, code: str, position: str, gender: Optional[str] = None) -> List[Dict]:
        """
        Get syllable patterns for a specific position and optional gender.
        
        Args:
            code: Culture code
            position: Position in word ('initial', 'medial', 'final')
            gender: Optional gender for gender-specific patterns
            
        Returns:
            List of pattern dictionaries with weights
        """
        culture = self.get_culture(code)
        if not culture:
            return []
        
        patterns = []
        
        # Get base patterns for the position
        base_patterns = culture.get("syllable_patterns", {}).get(position, [])
        patterns.extend(base_patterns)
        
        # Add gender-specific patterns if applicable
        if gender:
            gender_patterns = culture.get("gender_patterns", {}).get(gender, {}).get(position, [])
            if gender_patterns:
                # Gender-specific patterns override base patterns
                pattern_strings = [p["pattern"] for p in gender_patterns]
                # Remove base patterns that are overridden
                patterns = [p for p in patterns if p["pattern"] not in pattern_strings]
                patterns.extend(gender_patterns)
        
        return patterns
    
    def get_constraints(self, code: str) -> Dict[str, Any]:
        """
        Get phonotactic constraints for a culture.
        
        Args:
            code: Culture code
            
        Returns:
            Dictionary of constraints
        """
        culture = self.get_culture(code)
        if not culture:
            return {}
        
        return culture.get("constraints", {})
    
    def get_style_preferences(self, code: str) -> Dict[str, Any]:
        """
        Get style preferences for a culture.
        
        Args:
            code: Culture code
            
        Returns:
            Dictionary of style preferences
        """
        culture = self.get_culture(code)
        if not culture:
            return {}
        
        return culture.get("style", {})
    
    def get_morphology(self, code: str) -> Dict[str, Any]:
        """
        Get morphological components (prefixes/suffixes) for a culture.
        
        Args:
            code: Culture code
            
        Returns:
            Dictionary of morphological components
        """
        culture = self.get_culture(code)
        if not culture:
            return {}
        
        return culture.get("morphology", {})
    
    def get_examples(self, code: str, gender: Optional[str] = None) -> List[str]:
        """
        Get example names for a culture.
        
        Args:
            code: Culture code
            gender: Optional gender filter
            
        Returns:
            List of example names
        """
        culture = self.get_culture(code)
        if not culture:
            return []
        
        examples = culture.get("examples", {})
        
        if gender and gender in examples:
            return examples[gender]
        
        # Return all examples if no gender specified
        all_examples = []
        for gender_examples in examples.values():
            all_examples.extend(gender_examples)
        
        return all_examples
    
    def reload_culture(self, code: str) -> bool:
        """
        Reload a specific culture from disk.
        Useful for hot-reloading during development.
        
        Args:
            code: Culture code to reload
            
        Returns:
            True if successful, False otherwise
        """
        filepath = self.culture_dir / f"{code}.json"
        
        if not filepath.exists():
            # Try to find by matching code in existing files
            for file in self.culture_dir.glob("*.json"):
                try:
                    data = self._load_culture_file(file)
                    if data.get("code") == code:
                        filepath = file
                        break
                except:
                    continue
            else:
                logger.error(f"Culture file not found for code: {code}")
                return False
        
        try:
            culture_data = self._load_culture_file(filepath)
            if self._validate_culture(culture_data):
                self._cultures[code] = culture_data
                logger.info(f"Reloaded culture: {culture_data['name']} ({code})")
                return True
            else:
                logger.error(f"Invalid culture data for code: {code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to reload culture {code}: {e}")
            return False
    
    def reload_all_cultures(self) -> Dict[str, Dict]:
        """
        Reload all cultures from disk.
        
        Returns:
            Updated dictionary of all cultures
        """
        self._cultures.clear()
        return self.load_all_cultures()
    
    @lru_cache(maxsize=128)
    def get_weighted_pattern(self, code: str, position: str, gender: Optional[str] = None) -> Optional[str]:
        """
        Get a random pattern weighted by probability.
        This is cached for performance.
        
        Args:
            code: Culture code
            position: Position in word
            gender: Optional gender
            
        Returns:
            Selected pattern string or None
        """
        import random
        
        patterns = self.get_syllable_patterns(code, position, gender)
        if not patterns:
            return None
        
        # Extract patterns and weights
        pattern_list = [p["pattern"] for p in patterns]
        weights = [p.get("weight", 1.0) for p in patterns]
        
        # Weighted random selection
        return random.choices(pattern_list, weights=weights)[0]
    
    def get_culture_info(self, code: str) -> Dict[str, Any]:
        """
        Get a summary of culture information suitable for API responses.
        
        Args:
            code: Culture code
            
        Returns:
            Dictionary with culture information
        """
        culture = self.get_culture(code)
        if not culture:
            return {}
        
        style = culture.get("style", {})
        length_range = style.get("length_range", {})
        
        return {
            "code": culture["code"],
            "name": culture["name"],
            "description": culture["description"],
            "typical_length": f"{length_range.get('min', 3)}-{length_range.get('max', 12)} characters",
            "ideal_syllables": style.get("ideal_syllable_count", 2),
            "common_sounds": {
                "consonants": culture["phonemes"]["consonants"][:10] + "...",
                "vowels": culture["phonemes"]["vowels"]
            },
            "example_names": self.get_examples(code)[:5],  # Just first 5 examples
            "supports_gender": bool(culture.get("gender_patterns"))
        }
    
    def __repr__(self):
        return f"<CultureLoader: {len(self._cultures)} cultures loaded>"

# Create a singleton instance that can be imported
_culture_loader_instance = None

def get_culture_loader() -> CultureLoader:
    """
    Get the singleton CultureLoader instance.
    
    Returns:
        CultureLoader instance
    """
    global _culture_loader_instance
    
    if _culture_loader_instance is None:
        _culture_loader_instance = CultureLoader()
        _culture_loader_instance.load_all_cultures()
    
    return _culture_loader_instance