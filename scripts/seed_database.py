# scripts/seed_database.py
# Run this script after initial installation or to reset the db
# python scripts/seed_database.py
# Optional Flags:
#--reset, --verbose, --test, --create-files, --db-url <url>

import os
import sys
import json
import argparse

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm import declarative_base

Base = declarative_base()

from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey, Text

# Database Models
class Culture(Base):
    __tablename__ = 'cultures'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    code = Column(String(10), nullable=False, unique=True)
    description = Column(Text)
    config = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SyllablePattern(Base):
    __tablename__ = 'syllable_patterns'
    
    id = Column(Integer, primary_key=True)
    culture_id = Column(Integer, ForeignKey('cultures.id'), nullable=False)
    pattern_type = Column(String(20), nullable=False)
    pattern = Column(String(20), nullable=False)
    weight = Column(Float, default=1.0)
    gender = Column(String(20), nullable=True)

class GeneratedName(Base):
    __tablename__ = 'generated_names'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    culture_id = Column(Integer, ForeignKey('cultures.id'), nullable=False)
    gender = Column(String(20))
    pronunciation = Column(String(100))
    syllables = Column(JSON)
    score = Column(Float)
    parameters = Column(JSON)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

# Culture loader
def load_culture_from_file(filepath: Path) -> Dict:
    # Load culture configuration from a JSON file to ensure seed data matches runtime exactly
    with open(filepath, 'r') as f:
        return json.load(f)
    
def get_culture_files() -> List[Path]:
    # Get all culture JSON files from the cultures directory
    culture_dir = Path(__file__).parent.parent / "app" / "data" / "cultures"

    if not culture_dir.exists():
        culture_dir = Path(__file__).parent / "test_cultures"
        culture_dir.mkdir(exist_ok=True)

        test_elvish = culture_dir / "elvish.json"
        if not test_elvish.exists():
            create_default_cultures(culture_dir)

    return list(culture_dir.glob("*.json"))

def create_default_cultures(culture_dir: Path):
    # Create defult culture files if they dont exist for testing
    print(f"Creating default cultures in {culture_dir}")
    
    # Elvish culture
    elvish = {
        "name": "Elvish",
        "code": "elv",
        "description": "Flowing, melodic names with soft consonants and vowel harmony",
        "phonemes": {
            "consonants": "lmnrsvwy",
            "vowels": "aeiouy",
            "liquids": "lr",
            "nasals": "mn",
            "sibilants": "s"
        },
        "syllable_patterns": {
            "initial": [
                {"pattern": "V", "weight": 2.0},
                {"pattern": "CV", "weight": 3.0},
                {"pattern": "LV", "weight": 2.5}
            ],
            "medial": [
                {"pattern": "CV", "weight": 3.0},
                {"pattern": "V", "weight": 1.0},
                {"pattern": "LV", "weight": 2.0},
                {"pattern": "CVC", "weight": 1.5}
            ],
            "final": [
                {"pattern": "V", "weight": 2.5},
                {"pattern": "VC", "weight": 1.5},
                {"pattern": "VL", "weight": 2.0},
                {"pattern": "VN", "weight": 1.8}
            ]
        },
        "gender_patterns": {
            "feminine": {
                "initial": [{"pattern": "V", "weight": 3.0}, {"pattern": "LV", "weight": 2.5}],
                "final": [{"pattern": "V", "weight": 3.0}, {"pattern": "VL", "weight": 2.5}]
            },
            "masculine": {
                "initial": [{"pattern": "CV", "weight": 3.0}, {"pattern": "CVC", "weight": 2.0}],
                "final": [{"pattern": "VC", "weight": 2.0}, {"pattern": "VN", "weight": 2.0}]
            }
        },
        "constraints": {
            "forbidden_clusters": ["ml", "nm", "sr", "wr"],
            "forbidden_initial": ["y", "w"],
            "forbidden_final": ["w"],
            "max_consonant_cluster": 2,
            "vowel_harmony": True
        },
        "style": {
            "prefer_vowel_endings": True,
            "ideal_syllable_count": 3,
            "length_range": {"min": 3, "max": 12, "ideal": 7}
        },
        "morphology": {
            "prefixes": {
                "masculine": ["Ael", "El", "Gal", "Fin"],
                "feminine": ["Ara", "Ela", "Lyr", "Sil"]
            },
            "suffixes": {
                "masculine": ["ion", "dir", "las", "orn"],
                "feminine": ["iel", "wen", "eth", "yn"]
            }
        },
        "examples": {
            "masculine": ["Elrond", "Legolas", "Thranduil", "Finarfin"],
            "feminine": ["Arwen", "Galadriel", "Nimrodel", "Elaria"]
        }
    }
    
    # Dwarven culture
    dwarven = {
        "name": "Dwarven",
        "code": "dwf",
        "description": "Strong, consonant-heavy names with hard sounds",
        "phonemes": {
            "consonants": "bdfgkmnprst",
            "vowels": "aeiou",
            "liquids": "r",
            "nasals": "mn",
            "stops": "bdgkpt"
        },
        "syllable_patterns": {
            "initial": [
                {"pattern": "CVC", "weight": 3.0},
                {"pattern": "CV", "weight": 2.0},
                {"pattern": "CCVC", "weight": 2.5}
            ],
            "medial": [
                {"pattern": "CVC", "weight": 3.0},
                {"pattern": "CV", "weight": 1.5},
                {"pattern": "VC", "weight": 2.0},
                {"pattern": "CCVC", "weight": 2.0}
            ],
            "final": [
                {"pattern": "VC", "weight": 3.0},
                {"pattern": "VCC", "weight": 2.5},
                {"pattern": "VN", "weight": 2.0},
                {"pattern": "V", "weight": 0.5}
            ]
        },
        "gender_patterns": {
            "feminine": {
                "final": [{"pattern": "V", "weight": 2.0}, {"pattern": "VC", "weight": 2.0}]
            },
            "masculine": {
                "final": [{"pattern": "VCC", "weight": 3.0}, {"pattern": "VC", "weight": 2.5}]
            }
        },
        "constraints": {
            "forbidden_clusters": [],
            "forbidden_initial": [],
            "forbidden_final": ["e"],
            "max_consonant_cluster": 3,
            "allow_double_consonants": True
        },
        "style": {
            "prefer_consonant_clusters": True,
            "ideal_syllable_count": 2,
            "length_range": {"min": 4, "max": 10, "ideal": 6}
        },
        "morphology": {
            "prefixes": {
                "masculine": ["Thor", "Grim", "Dur", "Bal"],
                "feminine": ["Dis", "Dwal", "Nar", "Kil"]
            },
            "suffixes": {
                "masculine": ["in", "orn", "ur", "im"],
                "feminine": ["a", "i", "is", "ila"]
            }
        },
        "examples": {
            "masculine": ["Thorin", "Gimli", "Balin", "Dwalin"],
            "feminine": ["Disa", "Kili", "Nari", "Dwala"]
        }
    }
    
    # Human culture
    human = {
        "name": "Human",
        "code": "hum",
        "description": "Versatile names with balanced phonetics",
        "phonemes": {
            "consonants": "bcdfghjklmnprstvwz",
            "vowels": "aeiou",
            "liquids": "lr",
            "nasals": "mn"
        },
        "syllable_patterns": {
            "initial": [
                {"pattern": "CV", "weight": 3.0},
                {"pattern": "CVC", "weight": 2.0},
                {"pattern": "V", "weight": 1.0}
            ],
            "medial": [
                {"pattern": "CV", "weight": 3.0},
                {"pattern": "CVC", "weight": 2.5},
                {"pattern": "V", "weight": 1.5},
                {"pattern": "VC", "weight": 1.5}
            ],
            "final": [
                {"pattern": "VC", "weight": 2.5},
                {"pattern": "V", "weight": 2.0},
                {"pattern": "CVC", "weight": 1.5},
                {"pattern": "VN", "weight": 2.0}
            ]
        },
        "gender_patterns": {
            "feminine": {
                "final": [{"pattern": "V", "weight": 3.0}, {"pattern": "VN", "weight": 1.5}]
            },
            "masculine": {
                "final": [{"pattern": "VC", "weight": 3.0}, {"pattern": "VCC", "weight": 1.5}]
            }
        },
        "constraints": {
            "forbidden_clusters": ["bk", "pd", "kg"],
            "forbidden_initial": ["x", "z"],
            "forbidden_final": [],
            "max_consonant_cluster": 2
        },
        "style": {
            "balanced_consonants": True,
            "ideal_syllable_count": 2,
            "length_range": {"min": 3, "max": 10, "ideal": 6}
        },
        "morphology": {
            "prefixes": {
                "masculine": ["Gar", "Mar", "Bran", "Cor"],
                "feminine": ["Ela", "Mira", "Sara", "Ana"]
            },
            "suffixes": {
                "masculine": ["eth", "ard", "win", "ric"],
                "feminine": ["a", "ella", "ine", "ara"]
            }
        },
        "examples": {
            "masculine": ["Gareth", "Marcus", "Brandon", "Aldric"],
            "feminine": ["Elena", "Mirabelle", "Seraphina", "Clara"]
        }
    }
    
    # Save the culture files
    with open(culture_dir / "elvish.json", 'w') as f:
        json.dump(elvish, f, indent=2)
    
    with open(culture_dir / "dwarven.json", 'w') as f:
        json.dump(dwarven, f, indent=2)
    
    with open(culture_dir / "human.json", 'w') as f:
        json.dump(human, f, indent=2)
    
    print(f"✓ Created 3 default culture files in {culture_dir}")

# Seeding functions
def seed_cultures(session: Session, verbose: bool = False) -> Dict[str, int]:
    print("\nSeeding cultures from JSON files...")

    culture_files = get_culture_files()
    culture_ids = {}

    for filepath in culture_files:
        try:
            culture_data = load_culture_from_file(filepath)

            existing = session.query(Culture).filter_by(code=culture_data['code']).first()

            if existing:
                if verbose:
                    print(f" - Updating culture: {culture_data['name']}")
                
                existing.name = culture_data['name']
                existing.description = culture_data["description"]
                existing.config = culture_data
                existing.updated_at = datetime.utcnow()
                culture_ids[culture_data["code"]] = existing.id

            else:
                culture = Culture(
                    name=culture_data["name"],
                    code=culture_data["code"],
                    description=culture_data["description"],
                    config=culture_data
                )
                session.add(culture)
                session.flush()
                culture_ids[culture_data["code"]] = culture.id
                if verbose:
                    print(f" - Added culture: {culture_data['name']}")
        
        except Exception as e:
            print(f" ! Error loading culture from {filepath}: {e}")
    
    session.commit()
    print(f"✓ Seeded {len(culture_ids)} cultures.")
    return culture_ids

def seed_syllable_patterns(session: Session, culture_ids: Dict[str, int], verbose: bool = False):
    print("\nSeeding syllable patterns...")

    pattern_count = 0
    culture_files = get_culture_files()

    for filepath in culture_files:
        culture_data = load_culture_from_file(filepath)
        culture_id = culture_ids.get(culture_data['code'])

        if not culture_id:
            continue

        session.query(SyllablePattern).filter_by(culture_id=culture_id).delete()

        for position in ["initial", "medial", "final"]:
            patterns = culture_data.get("syllable_patterns", {}).get(position, [])
            for pattern_data in patterns:
                sp = SyllablePattern(
                    culture_id=culture_id,
                    pattern_type=position,
                    pattern=pattern_data["pattern"],
                    weight=pattern_data.get("weight", 1.0),
                    gender=None
                )
                session.add(sp)
                pattern_count += 1
        
        gender_patterns = culture_data.get("gender_patterns", {})
        for gender, positions in gender_patterns.items():
            for position, patterns in positions.items():
                for pattern_data in patterns:
                    sp = SyllablePattern(
                        culture_id=culture_id,
                        pattern_type=position,
                        pattern=pattern_data["pattern"],
                        weight=pattern_data.get("weight", 1.0),
                        gender=gender
                    )
                    session.add(sp)
                    pattern_count += 1
    
    session.commit()
    print(f"✓ Seeded {pattern_count} syllable patterns.")

def seed_sample_names(session: Session, culture_ids: Dict[str, int], verbose: bool = False):
    print("\nSeeding sample generated names...")

    name_count = 0
    culture_files = get_culture_files()

    for filepath in culture_files:
        culture_data = load_culture_from_file(filepath)
        culture_id = culture_ids.get(culture_data["code"])

        if not culture_id:
            continue

        examples = culture_data.get("examples", {})

        for gender, names in examples.items():
            for name in names:
                existing = session.query(GeneratedName).filter_by(
                    name=name,
                    culture_id=culture_id
                ).first()

                if not existing:
                    syllables = [name[i:i+2] for i in range(0, len(name), 2)]
                    if len(name) % 2 == 1:
                        syllables[-1] = name[-(3 if len(name) > 2 else 1):]

                    generated_name = GeneratedName(
                        name=name,
                        culture_id=culture_id,
                        gender=gender if gender != "neutral" else None,
                        pronunciation="-".join(s.lower() for s in syllables),
                        syllables=syllables,
                        score=0.9, # high score for examples
                        parameters={"seed": True, "source": "examples"},
                        usage_count=0
                    )
                    session.add(generated_name)
                    name_count += 1

                    if verbose:
                        print(f" - Added {gender} {culture_data['name']} name: {name}")
    
    session.commit()
    print(f"✓ Seeded {name_count} sample names.")

def verify_seeding(session: Session):
    print("\n" + "="*50)
    print("DATABASE SEEDING COMPLETE - VERIFICATION")
    print("="*50 + "\n")

    culture_count = session.query(Culture).count()
    print(f"Total Cultures: {culture_count}")

    for culture in session.query(Culture).all():
        pattern_count = session.query(SyllablePattern).filter_by(
            culture_id=culture.id
        ).count()

        pattern_types = session.query(SyllablePattern.pattern_type).filter_by(
            culture_id=culture.id
        ).distinct().all()
        types = [pt[0] for pt in pattern_types]

        print(f" - {culture.name}: {pattern_count} patterns ({', '.join(types)})")

    total_names = session.query(GeneratedName).count()
    print(f"\nSample names: {total_names}")

    for culture in session.query(Culture).all():
        for gender in ['masculine', 'feminine', None]:
            count = session.query(GeneratedName).filter_by(
                culture_id=culture.id,
                gender=gender
            ).count()
            if count > 0:
                gender_label = gender or 'neutral'
                print(f" - {culture.name} ({gender_label}): {count} names")

    print("\n✓ Database seeding verification complete.")

def main():
    parser = argparse.ArgumentParser(
        description='Initialize the Name Generator database with culture data from JSON files'
    )
    parser.add_argument('--reset', action='store_true', help='Drop all existing tables before seeding')
    parser.add_argument('--verbose', action='store_true', help='Show detailed progress')
    parser.add_argument('--test', action='store_true', help='Use test database')
    parser.add_argument('--create-files', action='store_true', help='Create default culture JSON files if missing')
    parser.add_argument('--db-url', type=str, help='Override database URL')
    
    args = parser.parse_args()
    
    # Determine database URL
    if args.db_url:
        database_url = args.db_url
    elif args.test:
        database_url = "sqlite:///./test_name_generator.db"
    else:
        database_url = os.getenv('DATABASE_URL', 'sqlite:///./name_generator.db')
    
    print(f"Using database: {database_url}")
    
    # Create default culture files if requested
    if args.create_files:
        culture_dir = Path(__file__).parent.parent / "app" / "data" / "cultures"
        culture_dir.mkdir(parents=True, exist_ok=True)
        create_default_cultures(culture_dir)
        return
    
    # Create engine and session
    engine = create_engine(database_url, echo=args.verbose)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Reset if requested
    if args.reset:
        confirm = input("⚠️  This will DELETE all existing data. Continue? (y/N): ")
        if confirm.lower() == 'y':
            Base.metadata.drop_all(bind=engine)
        else:
            print("Aborted.")
            return
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables ready")
    
    # Seed the database
    with SessionLocal() as session:
        try:
            # Seed from JSON files
            culture_ids = seed_cultures(session, args.verbose)
            seed_syllable_patterns(session, culture_ids, args.verbose)
            seed_sample_names(session, culture_ids, args.verbose)
            
            # Verify
            verify_seeding(session)
            
        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            session.rollback()
            raise


if __name__ == "__main__":
    main()
