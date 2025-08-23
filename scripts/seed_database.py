# scripts/seed_database.py
# Run this script after initial installation or to reset the db
# python scripts/seed_database.py
# Optional Flags:
#--reset, --verbose, --test

import os
import sys
import json
import argparse
from pathlib import path
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# import models
Base = declarative_base()

from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, ForeignKey, Text

# these mirror the models in the app/models/database.py but are defined here to make script self-contained

class Culture(Base):
    __tablename__ = 'cultures'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    code = Column(String(10), nullable=False, unique=True)
    description = Column(Text)
    config = Column(JSON, nullable=False) # stores culture specific rules
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SyllablePattern(Base):
    __tablename__ = 'syllable_patterns'

    id = Column(Integer, primary_key=True)
    culture_id = Column(Integer, ForeignKey('cultures_id'), nullable=False)
    pattern_type = Column(String(20), nullable=False) # 'initial', 'medial', 'final'
    pattern = Column(String(20), nullable=False) # 'cv', 'cvc', 'vc', etc
    weight = Column(Float, default=1.0) # probability weight for random selection
    gender = Column(String(20)) # NULL for any

class GeneratedName(Base):
    # cache of previously generated names with metadata
    # can leverage this to further even out the distribution
    __tablename__ = 'generated_names'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    culture_id = Column(Integer, ForeignKey('cultures.id'), nullable=False)
    gender = Column(String(20))
    pronounciation = Column(String(100))
    syllables = Column(JSON) # syllable components
    score = Column(Float) # pronounciation
    parameters = Column(JSON)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

# Linguistic rules for each culture
# Config consists of Phoneme sets, Phonotactic constraints, morphological patterns, style parameters, and examples for reference (future AI context)
ELVISH_CONFIG = {
    "name": "Elvish",
    "code": "elv",
    "description": "Flowing, melodic names with soft consonants and vowel harmony",
    "config": {
        "consonants": "lmnrsvwy",
        "vowels": "aeiouy",
        "liquids": "lr",
        "nasals": "mn",
        "sibilants": "s",

        "forbidden_clusters": ["ml", "nm", "sr", "wr"],
        "forbidden_initial": ["y", "w"],
        "forbidden_final": ["w"],
        "vowel_harmony": True,

        "prefixes": {
            "masculine": ["Ael", "El", "Gal", "Fin"],
            "feminine": ["Ara", "Ela", "Lyr", "Sil"]
        },
        "suffixes": {
            "masculine": ["ion", "dir", "las", "orn"],
            "feminine": ["iel", "wen", "eth", "yn"]
        },

        "prefer_vowel_endings": True,
        "max_consonant_cluster": 2,
        "ideal_syllable_count": 3,

        "examples": {
            "masculine": ["Elrond", "Legolas", "Thranduil", "Finarfin"],
            "feminine": ["Arwen", "Galadriel", "Nimrodel", "Elaria"]
        }
    }
}

DWARVEN_CONFIG = {
    "name": "Dwarven",
    "code": "dwf",
    "description": "Strong, consonant-heavy names with hard sounds and clan markers",
    "config": {
        "consonants": "bdfgkmnprst",
        "vowels": "aeiou",
        "liquids": "r",
        "nasals": "mn",
        "stops": "bdgkpt",

        "forbidden_clusters": [], #lots of consonant clusters - slavic origins?
        "forbidden_initial": [],
        "forbidden_final": ["e"],
        "allow_double_consonants": True,

        "prefixes": {
            "masculine": ["Thor", "Grim", "Dur", "Bal"],
            "feminine": ["Dis", "Dwal", "Nar", "Kil"]
        },
        "suffixes": {
            "masculine": ["in", "orn", "ur", "im"],
            "feminine": ["a", "i", "is", "ila"]
        },

        "prefer_consonant_clusters": True,
        "max_consonant_cluster": 3,
        "ideal_syllable_count": 2,

        "examples": {
            "masculine": ["Thorin", "Gimli", "Balin", "Dwalin", "Durin"],
            "feminine": ["Disa", "Kili", "Nari", "Dwala"]
        }
    }
}

#TODO: Need more delineation than just "human" but AI has digital boner for LOTR so it's wevz for now
HUMAN_CONFIG = {
    "name": "Human",
    "code": "hum",
    "description": "Versatile names with balanced phoenitics, regional variations",
    "config": {
        "consonants": "bcdfghjklmnprstvwz",
        "vowels": "aeiouy",
        "liquids": "lr",
        "nasals": "mn",

        "forbidden_clusters": ["bk", "pd", "kg"],
        "forbidden_initial": ["e", "s", "x"], # prevent emily chens, sylas, and xanders
        "forbidden_final": [],

        # regional variations (subcultures) to expand on later
        "regions": {
            "slavic": {
                "consonants": "bdfgklmnprst",
                "prefer_short": True
            },
            "imperial": { # you know who you are
                "consonants": "cflmnrsvw",
                "prefer_long": False
            }
        },

        "prefixes": {
            "masculine": ["Gar", "Mar", "Bran", "Cor"],
            "feminine": ["Am", "Ca", "Cr", "Sar"]
        },
        "suffixes": {
            "masculine": ["eth", "ard", "win", "ric"],
            "feminine": ["a", "ella", "ine", "ara"]
        },

        "balanced_consonants": True,
        "max_consonant_cluster": 3,
        "ideal_syllable_count": 2,

        "examples": {
            "masculine": ["Gareth", "Marcus", "Brandon", "Aldric"],
            "feminine": ["Amber", "Catherine", "Seraphina", "Clara"]
        }
    }
}

SYLLABLE_PATTERNS = {
    "elvish": {
        "initial": [
            ("V", 2.0),
            ("CV", 3.0),
            ("LV", 2.5),
        ],
        "medial": [
            ("CV", 3.0),
            ("V", 1.0),
            ("LV", 2.0),
            ("CVC", 1.5),
        ],
        "final": [
            ("V", 2.5),
            ("VC", 1.5),
            ("VL", 2.0),
            ("VN", 1.8),
        ],
        "gender_specific": {
            "feminine": {
                "final": [("V", 3.0), ("VL", 2.5)]
            },
            "masculine": {
                "final": [("VC", 2.0), ("VN", 2.0)]
            }
        }
    },
    "dwarven": {
        "initial": [
            ("CVC", 3.0),
            ("CV", 2.0),
            ("CCVC", 2.5),
        ],
        "medial": [
            ("CVC", 3.0),
            ("CV", 1.5),
            ("VC", 2.0),
            ("CCVC", 2.0),
        ],
        "final": [
            ("VC", 3.0),
            ("VCC", 2.5),
            ("VN", 2.0),
            ("V", 0.5),
        ],
        "gender_specific": {
            "feminine": {
                "final": [("V", 2.0), ("VC", 2.0)]
            },
            "masculine": {
                "final": [("VCC", 3.0), ("VC", 2.5)]
            }
        }
    },
    "human": {
        "initial": [
            ("CV", 3.0),
            ("CVC", 2.0),
            ("V", 1.0),
        ],
        "medial": [
            ("CV", 3.0),
            ("CVC", 2.5),
            ("V", 1.5),
            ("VC", 1.5)
        ],
        "final": [
            ("VC", 2.5),
            ("V", 2.0),
            ("CVC", 1.5),
            ("VN", 2.0),
        ],
        "gender_specific": {
            "feminine": {
                "final": [("V", 3.0), ("VN", 1.5)]
            },
            "masculine": {
                "final": [("VC", 3.0), ("VCC", 1.5)]
            }
        }
    }
}

SAMPLE_NAMES = {
    "elvish": {
        "masculine": [
            ("Aelion", ["Ae", "li", "on"], 0.92),
            ("Silvain", ["Sil", "va", "in"], 0.89),
            ("Elyndor", ["E", "lyn", "dor"], 0.87),
            ("Finrael", ["Fin", "ra", "el"], 0.91),
            ("Lorenir", ["Lo", "re", "nir"], 0.88),
        ],
        "feminine": [
            ("Lyralei", ["Ly", "ra", "lei"], 0.93),
            ("Elowen", ["E", "lo", "wen"], 0.94),
            ("Silveth", ["Sil", "veth"], 0.90),
            ("Aranel", ["A", "ra", "nel"], 0.91),
            ("Nimriel", ["Nim", "ri", "el"], 0.92),
        ]
    },
    "dwarven": {
        "masculine": [
            ("Thormund", ["Thor", "mund"], 0.88),
            ("Grimkor", ["Grim", "kor"], 0.87),
            ("Durgan", ["Dur", "gan"], 0.89),
            ("Baldin", ["Bal", "din"], 0.86),
            ("Kromli", ["Krom", "li"], 0.85),
        ],
        "feminine": [
            ("Diska", ["Dis", "ka"], 0.84),
            ("Narila", ["Na", "ri", "la"], 0.83),
            ("Dwali", ["Dwa", "li"], 0.82),
            ("Kildis", ["Kil", "dis"], 0.85),
            ("Bruni", ["Bru", "ni"], 0.81),
        ]
    },
    "human": {
        "masculine": [
            ("Marcus", ["Mar", "cus"], 0.95),
            ("Gareth", ["Ga", "reth"], 0.94),
            ("Brandon", ["Bran", "don"], 0.93),
            ("Corin", ["Co", "rin"], 0.92),
            ("Aldric", ["Al", "dric"], 0.91),
        ],
        "feminine": [
            ("Elena", ["E", "le", "na"], 0.96),
            ("Mirabelle", ["Mi", "ra", "belle"], 0.94),
            ("Sera", ["Se", "ra"], 0.95),
            ("Clara", ["Cla", "ra"], 0.97),
            ("Anara", ["A", "na", "ra"], 0.93),
        ]
    }
}

# Database seeding functions

def create_tables(engine):
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully")

def drop_tables(engine):
    print("Dropping existing tables")
    Base.metadata.drop_all(bind=engine)
    print("Tables dropped!")

def seed_cultures(session: Session, verbose: bool = False):
    print("\nSeeding Cultures")

    cultures = [
        (ELVISH_CONFIG["name"], ELVISH_CONFIG["code"],
        ELVISH_CONFIG["description"], ELVISH_CONFIG["config"]),
        (DWARVEN_CONFIG["name"], DWARVEN_CONFIG["code"],
        DWARVEN_CONFIG["description"], DWARVEN_CONFIG["config"]),
        (HUMAN_CONFIG["name"], HUMAN_CONFIG["code"],
        HUMAN_CONFIG["description"], HUMAN_CONFIG["config"]),
    ]

    culture_ids = {}

    for name, code, description, config in cultures:
        existing = session.query(Culture).filter_by(code=code).first()

        if existin:
            if verbose:
                print(f" - Culture '{name}' already exists, updating...")
            existing.config = config
            existing.updated_at = datetime.utcnow()
            culture_ids[code] = existing.id
        else:
            culture = Culture(
                name=name,
                code=code,
                description=description,
                config=config
            )    
            session.add(culture)
            session.flush()
            culture_ids[code] = culture.id
            if verbose:
                print(f" Added Culture: {name}")

    session.commit()
    print(f"Seeded {len(cultures)} cultures")
    return culture_ids

def seed_syllable_patterns(session: Session, culture_ids: Dict[str, int], verbose: bool = False):
    print("\nSeeding syllable patterns")

    pattern_count = 0

    for culture_name, patterns in SYLLABLE_PATTERNS.items():
        culture_code = {
            "elvish": "elv",
            "dwarven": "dwf",
            "human": "hum"
        }[culture_name]

        culture_id = culture_ids[culture_code]

        session.query(SyllablePattern).filter_by(culture_id=culture_id).delete()

        for position in ["initial", "medial", "final"]:
            if position in patterns:
                for pattern, weight in patterns[position]:
                    sp = SyllablePattern(
                        culture_id=culture_id,
                        pattern_type=position,
                        pattern=pattern,
                        weight=weight,
                        gender=None
                    )
                    session.add(sp)
                    pattern_count += 1

        if "gender_specific" in patterns:
            for gender, gender_patterns in patterns["gender_specific"].items():
                for position, position_patterns in gender_patterns.items():
                    for pattern, weight in position_patterns:
                        sp = SyllablePattern(
                            culture_id=culture_id,
                            pattern_type=position,
                            pattern=pattern,
                            weight=weight,
                            gender=gender
                        )
                        session.add(sp)
                        pattern_count += 1

    session.commit()
    print(f" Seeded {pattern_count} syllable patterns")

def seed_sample_names(session: Session, culture_ids: Dict[str, int], verbose: bool = False):
    print("\nSeeding sample names.")

    name_count = 0

    for culture_name, genders in SAMPLE_NAMES.items():
        culture_code = {
            "elvish": "elv",
            "dwarven": "dwf",
            "human": "hum"
        }[culture_name]

        culture_id = culture_ids[culture_code]

        for gender, names in genders.items():
            for name, syllables, score in names:
                existing = session.query(GeneratedName).filter_by(
                    name=name,
                    culture_id=culture_ids
                ).first()

                if not existing:
                    # simple MVP pronounciation
                    pronunciation = '-'.join(s.lower() for s in syllables)

                    generated_name = GeneratedName(
                        name=name,
                        culture_id=culture_id,
                        gender=gender,
                        pronunciation=pronunciation,
                        syllables=syllables,
                        score=score,
                        parameters={
                            "culture": culture_code,
                            "gender": gender,
                            "seed": True
                            
                        },
                        usage_count=0
                    )
                    session.add(generated_name)
                    name_count += 1

                    if verbose:
                        print(f"Added {gender} {culture_name} name: {name}")
    session.commit()
    print(f"Seeded {name_count} sample names")

def verify_seeding(session: Session):
    print("\n" + "="*50)
    print("DATABSE SEEDING COMPLETE - VERIFICATION")
    print("="*50)

    culture_count = session.query(Culture).count()
    print(f"Cultures: {culture_count}")

    for culture in session.query(Culture).all():
        pattern_count = session.query(SyllablePattern).filter_by(
            culture_id=culture.id
        ).count()
        print(f" - {culture.name}: {pattern_count} patterns")

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
                print(f" - {culture.name} ({gender_label}): {count}")

    print("\nDatabase seeding completed successfully!")

def main():
    parser = argparse.ArgumentParser(
        description='Initialize the Name Generator database with seed data'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Drop all existing tables before seeding'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed progress information'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Use test db instead of production'
    )
    parser.add_argument(
        '--db-url',
        type=str,
        help='Override database URL from environment'
    )

    args = parser.parse_args()

    if args.db_url:
        database_url = args.db_url
    elif args.test:
        database_url = "sqlite:///./test_name_generator.db"
    else:
        database_url = os.getenv('DATABASE_URL', 'sqlite:///./name_generator.db')

    print(f"Using database: {database_url}")

    engine = create_engine(database_url, echo=args.verbose)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    if args.reset:
        confirm = input("This will DELETE all existing data. Continue? (y/N): ")
        if confirm.lower() == 'y':
            drop_tables(engine)
        else:
            print("Aborted.")
            return

    create_tables(engine)

    with SessionLocal() as session:
        try:
            culture_ids = seed_cultures(session, args.verbose)

            seed_syllable_patterns(session, culture_ids, args.verbose)

            seed_sample_names(session, culture_ids, args.verbose)

            verify_seeding(session)

        except Exception as e:
            print(f"\nError during seeding: {e}")
            session.rollback()
            raise

if __name__ == "__main__":
    main()
