# Complete Guide: Adding a New Culture to Name Generator

## Overview
Adding a new culture is designed to be straightforward - you create ONE JSON file, and the system handles the rest. Here's the complete process.

## Step 1: Create the Culture JSON File

**Location**: `app/data/cultures/nordic.json`

Create a new JSON file following the unified schema:

```json
{
  "name": "Nordic",
  "code": "nor",
  "description": "Strong, mythologically-inspired names with Old Norse influences",
  
  "phonemes": {
    "consonants": "bdfghjklmnrstvþ",
    "vowels": "aeiouyáæø",
    "liquids": "lr",
    "nasals": "mn",
    "fricatives": "fsvþ"
  },
  
  "syllable_patterns": {
    "initial": [
      {"pattern": "CV", "weight": 3.0},
      {"pattern": "CCV", "weight": 2.5},
      {"pattern": "V", "weight": 1.0}
    ],
    "medial": [
      {"pattern": "CV", "weight": 3.0},
      {"pattern": "CVC", "weight": 2.5},
      {"pattern": "VC", "weight": 2.0}
    ],
    "final": [
      {"pattern": "VC", "weight": 3.0},
      {"pattern": "VCC", "weight": 2.0},
      {"pattern": "V", "weight": 1.5}
    ]
  },
  
  "gender_patterns": {
    "feminine": {
      "final": [
        {"pattern": "V", "weight": 2.5},
        {"pattern": "VN", "weight": 2.0}
      ]
    },
    "masculine": {
      "final": [
        {"pattern": "VC", "weight": 3.0},
        {"pattern": "VCC", "weight": 2.5}
      ]
    }
  },
  
  "constraints": {
    "forbidden_clusters": ["þs", "þt"],
    "forbidden_initial": ["þ", "ø"],
    "forbidden_final": ["þ"],
    "max_consonant_cluster": 3,
    "allow_double_consonants": true
  },
  
  "style": {
    "prefer_strong_consonants": true,
    "ideal_syllable_count": 2,
    "length_range": {
      "min": 4,
      "max": 10,
      "ideal": 6
    }
  },
  
  "morphology": {
    "prefixes": {
      "masculine": ["Bjorn", "Thor", "Rag", "Sig"],
      "feminine": ["Ast", "Frey", "Gud", "Hil"]
    },
    "suffixes": {
      "masculine": ["nar", "mund", "vald", "stein"],
      "feminine": ["rid", "dis", "hild", "run"]
    }
  },
  
  "examples": {
    "masculine": ["Ragnar", "Bjorn", "Thorstein", "Sigurd"],
    "feminine": ["Astrid", "Freydis", "Brunhild", "Gudrun"]
  }
}
```

## Step 2: Update the Database

Run the seed script to add the new culture to the database:

```bash
# This will ADD the new culture without affecting existing data
python scripts/seed_database.py

# Or if you want to see details:
python scripts/seed_database.py --verbose
```

**What happens automatically:**
- ✅ The script detects the new `nordic.json` file
- ✅ Creates a new entry in the `cultures` table
- ✅ Adds all syllable patterns to `syllable_patterns` table
- ✅ Inserts example names into `generated_names` table
- ✅ Existing cultures remain untouched

## Step 3: Restart the Application

The application needs to reload to pick up the new culture:

```bash
# If running with uvicorn auto-reload (development):
# The app will automatically restart when it detects file changes

# If running in production:
# Restart your application server
systemctl restart name-generator  # or your deployment method
```

**What happens automatically:**
- ✅ `CultureLoader` detects and loads the new culture from JSON
- ✅ The culture becomes immediately available in the API
- ✅ All endpoints automatically include the new culture

## Step 4: Verify the New Culture

Test that your new culture is working:

```bash
# 1. Check it appears in the culture list
curl http://localhost:8000/api/v1/names/cultures

# 2. Generate some names
curl -X POST http://localhost:8000/api/v1/names/generate \
  -H "Content-Type: application/json" \
  -d '{"culture": "nordic", "count": 5}'

# 3. Check the health endpoint
curl http://localhost:8000/health
```

## What You DON'T Need to Update

These files/components handle the new culture automatically:

### ✅ **Automatically Updated**

1. **app/main.py** - No changes needed
   - `CultureLoader` loads all JSON files automatically
   
2. **app/api/v1/routes.py** - No changes needed
   - Endpoints work with any loaded culture

3. **app/core/generator.py** - No changes needed
   - Uses culture data from CultureLoader

4. **app/core/syllables.py** - No changes needed
   - Pattern interpreter works with any pattern

5. **app/core/phonetics.py** - No changes needed
   - Scoring applies universal rules

6. **app/models/schemas.py** - No changes needed*
   - *Unless you want to add the culture to the enum for API validation

7. **app/models/database.py** - No changes needed
   - Schema supports any culture

## Optional: Update API Validation

If you want strict API validation, update the Culture enum in `schemas.py`:

```python
# app/models/schemas.py
class Culture(str, Enum):
    ELVISH = "elvish"
    DWARVEN = "dwarven"
    HUMAN = "human"
    NORDIC = "nordic"  # Add your new culture here
```

**Note**: If you don't update this, the API will still work but won't validate the culture name at the Pydantic level.

## Optional: Culture-Specific Scoring

If your culture needs special pronunciation rules, add them to `phonetics.py`:

```python
# app/core/phonetics.py
def apply_cultural_adjustments(self, score, name, culture):
    # ... existing code ...
    
    elif culture == 'nordic':
        # Nordic names can have harsher consonant clusters
        if self._has_double_consonants(name):
            score += 0.05  # Bonus for authentic feel
        # Penalize if too soft
        if not any(c in 'bdfgktþ' for c in name):
            score -= 0.1  # Needs some hard consonants
```

## Development Workflow

### For Development (Hot Reload):
```bash
# 1. Create nordic.json
# 2. The app auto-reloads if using --reload flag
# 3. Test immediately
```

### For Production:
```bash
# 1. Create nordic.json in development
# 2. Test thoroughly
# 3. Deploy JSON file to production
# 4. Run: python scripts/seed_database.py
# 5. Restart application
# 6. Verify with health check
```

## Testing Your New Culture

Create a test script to validate your culture works correctly:

```python
# test_nordic.py
import requests
import json

# Test culture list
response = requests.get("http://localhost:8000/api/v1/names/cultures")
cultures = response.json()
assert any(c["code"] == "nor" for c in cultures), "Nordic culture not found!"

# Test name generation
response = requests.post(
    "http://localhost:8000/api/v1/names/generate",
    json={
        "culture": "nordic",
        "gender": "masculine",
        "count": 10
    }
)
data = response.json()
names = data["names"]

print("Generated Nordic names:")
for name_obj in names:
    print(f"  {name_obj['name']} (score: {name_obj['score']})")

# Verify scores are acceptable
assert all(n["score"] >= 0.6 for n in names), "Some names scored too low!"
print("\n✅ Nordic culture successfully added and working!")
```

## Rollback Process

If something goes wrong:

### Option 1: Remove the Culture Completely
```bash
# 1. Delete the JSON file
rm app/data/cultures/nordic.json

# 2. Remove from database
sqlite3 name_generator.db
DELETE FROM syllable_patterns WHERE culture_id = (SELECT id FROM cultures WHERE code = 'nor');
DELETE FROM generated_names WHERE culture_id = (SELECT id FROM cultures WHERE code = 'nor');
DELETE FROM cultures WHERE code = 'nor';

# 3. Restart application
```

### Option 2: Fix and Re-seed
```bash
# 1. Fix the nordic.json file
# 2. Re-run seeding (it will update existing)
python scripts/seed_database.py --verbose
# 3. Restart application
```

## Troubleshooting Common Issues

### Issue: Culture doesn't appear in API
**Solution**: Check that the JSON file is in the correct directory and restart the app

### Issue: Names score too low
**Solution**: Adjust syllable patterns to avoid difficult consonant clusters

### Issue: Names don't feel authentic
**Solution**: Review example names from the target culture and adjust phonemes/patterns

### Issue: Database constraint errors
**Solution**: The culture code must be unique - check it doesn't already exist

## Best Practices for New Cultures

1. **Research First**: Study real names from the culture/style
2. **Start Simple**: Begin with basic patterns, enhance later
3. **Test Incrementally**: Generate names and check scores at each step
4. **Use Real Examples**: Include actual names in the examples field
5. **Consider Gender**: Not all cultures need gender patterns
6. **Document Sources**: Add comments about your linguistic references

## Summary: The Complete Process

1. **Create** `app/data/cultures/[culture].json` ✏️
2. **Run** `python scripts/seed_database.py` 🗄️
3. **Restart** your application 🔄
4. **Test** the new culture via API ✅

That's it! The architecture is designed so that adding a culture is primarily a data task, not a code task. The system automatically integrates any properly-formatted culture JSON file.