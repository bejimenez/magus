# Magus API

An intelligent, culturally-aware name generation service designed for interactive AI storytelling platforms. This API creates pronounceable, meaningful names across multiple fantasy cultures with fine-grained control over style, gender, and phonetic properties.

## 🎯 Overview

The Magus API solves the problem of generic, uninspiring character names in dynamic storytelling systems. Unlike simple random generators, this service uses linguistic patterns, phonotactic rules, and cultural templates to create names that feel authentic and purposeful.

### Key Features

- **Multi-cultural name generation** (Elvish, Dwarven, Human, and extensible)
- **Phonetic scoring** for pronounceability
- **Gender-aware patterns** with cultural authenticity
- **Syllable-based construction** with pattern templates
- **Pronunciation guides** for generated names
- **Quality scoring** and validation
- **High-performance caching** for instant responses
- **RESTful API** with comprehensive documentation

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- SQLite3
- (Optional) Docker & Docker Compose
- (Optional) Redis for distributed caching

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/name-generator.git
cd name-generator
```

2. **Set up virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Initialize database**
```bash
python scripts/seed_database.py
```

6. **Run the server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Docker Installation

```bash
docker-compose up -d
```

## 📖 API Documentation

Once running, visit `http://localhost:8000/docs` for interactive Swagger documentation.

### Core Endpoints

#### Generate Names
```http
POST /api/v1/names/generate
Content-Type: application/json

{
  "culture": "elvish",
  "gender": "feminine",
  "count": 5,
  "length": "medium",
  "include_pronunciation": true,
  "min_score": 0.7
}
```

**Response:**
```json
{
  "names": [
    {
      "name": "Lyralei",
      "pronunciation": "lee-rah-lay",
      "syllables": ["Ly", "ra", "lei"],
      "score": 0.892,
      "culture": "elvish",
      "gender": "feminine"
    }
  ],
  "generation_time_ms": 23.4,
  "parameters": {...}
}
```

#### List Cultures
```http
GET /api/v1/names/cultures
```

#### Validate Name
```http
GET /api/v1/names/validate/{name}?culture=elvish
```

#### Random Name
```http
GET /api/v1/names/random?culture=dwarven&gender=masculine
```

## 🏗️ Architecture

### System Design

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│                 │     │              │     │             │
│  FastAPI Layer  │────▶│ Service Layer│────▶│ Core Engine │
│   (REST API)    │     │  (Business)  │     │ (Generation)│
│                 │     │              │     │             │
└─────────────────┘     └──────────────┘     └─────────────┘
         │                      │                    │
         └──────────┬───────────┴────────────────────┘
                    │
            ┌───────▼────────┐
            │                │
            │  SQLite Cache  │
            │   + Templates  │
            │                │
            └────────────────┘
```

### Project Structure

```
name-generator/
├── app/
│   ├── api/           # API endpoints and routing
│   ├── core/          # Name generation algorithms
│   ├── models/        # Data models and schemas
│   ├── services/      # Business logic layer
│   └── data/          # Culture templates and rules
├── tests/             # Test suites
├── scripts/           # Utility scripts
└── docs/              # Additional documentation
```

### Technology Stack

- **Framework**: FastAPI (async Python web framework)
- **Database**: SQLite (embedded, upgradeable to PostgreSQL)
- **Validation**: Pydantic
- **Testing**: Pytest
- **Documentation**: OpenAPI/Swagger
- **Caching**: In-memory + SQLite (Redis optional)

## 🧪 Testing

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=app tests/

# Specific test file
pytest tests/unit/test_generator.py

# With verbose output
pytest -v
```

### Test Categories

- **Unit Tests**: Core generation algorithms, scoring functions
- **Integration Tests**: API endpoints, database operations
- **Performance Tests**: Response time, batch generation
- **Quality Tests**: Name pronounceability, cultural accuracy

## 🎨 Culture Templates

Cultures are defined in JSON templates that specify phonetic patterns, syllable structures, and transformation rules.

### Example: Elvish Template

```json
{
  "name": "Elvish",
  "code": "elv",
  "consonants": "lmnrsvwy",
  "vowels": "aeiouy",
  "patterns": {
    "initial": ["V", "CV", "LV"],
    "medial": ["CV", "V", "LV"],
    "final": ["V", "VC", "VL"]
  },
  "gender_patterns": {
    "feminine": {
      "final": ["V", "VL"]
    }
  }
}
```

Pattern notation:
- `C` = Consonant
- `V` = Vowel
- `L` = Liquid (l, r)
- `N` = Nasal (m, n)

## 🔧 Configuration

Configuration via environment variables (`.env` file):

```env
# Application
APP_NAME="Name Generator API"
API_V1_PREFIX="/api/v1"

# Database
DATABASE_URL="sqlite:///./name_generator.db"

# Generation Settings
MAX_NAME_LENGTH=12
MIN_NAME_LENGTH=3
DEFAULT_COUNT=1
MAX_COUNT=20

# Performance
MIN_SCORE_THRESHOLD=0.6
CACHE_TTL=3600

# Optional Redis
USE_REDIS=false
REDIS_URL="redis://localhost:6379"
```

## 📊 Performance

### Benchmarks (MVP)

| Operation | Target | Actual |
|-----------|--------|--------|
| Single name generation | < 50ms | ~23ms |
| Batch (20 names) | < 200ms | ~156ms |
| Culture list | < 10ms | ~3ms |
| Name validation | < 20ms | ~8ms |

### Optimization Strategies

1. **Caching**: Three-tier caching system
2. **Pre-computation**: Culture templates loaded at startup
3. **Indexed lookups**: SQLite indexes on frequently queried columns
4. **Async operations**: Non-blocking I/O throughout

## 🗺️ Roadmap

### Current: MVP (v1.0)
- ✅ Basic syllable-based generation
- ✅ Three culture templates
- ✅ REST API
- ✅ Pronunciation scoring
- ✅ SQLite caching

### Phase 2: Phonetic Enhancement (v1.1)
- 🔄 IPA-based pronunciation
- 🔄 Phonotactic constraints
- 🔄 Markov chain transitions

### Phase 3: Morphological Components (v1.2)
- ⏳ Meaningful name parts
- ⏳ Etymology tracking
- ⏳ Semantic requests ("name meaning 'moonlight'")

### Phase 4: Cultural Enrichment (v1.3)
- ⏳ 10+ culture templates
- ⏳ Historical name patterns
- ⏳ Regional variations

### Phase 5: Neural Enhancement (v2.0)
- ⏳ ML-powered creativity
- ⏳ Style transfer
- ⏳ Cultural blending

See [ROADMAP.md](docs/ROADMAP.md) for detailed phase descriptions.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run linting
black app/ tests/
mypy app/

# Run tests before committing
pytest
```

### Contribution Areas

- **Culture Templates**: Add new fantasy/historical cultures
- **Phonetic Rules**: Improve pronunciation scoring
- **API Features**: Extend endpoints and capabilities
- **Performance**: Optimization and caching improvements
- **Documentation**: Examples, guides, and clarifications

## 📝 API Usage Examples

### Python Client

```python
import requests

# Generate elvish names
response = requests.post(
    "http://localhost:8000/api/v1/names/generate",
    json={
        "culture": "elvish",
        "gender": "feminine",
        "count": 3,
        "length": "medium"
    }
)
names = response.json()["names"]
```

### JavaScript/Node.js

```javascript
const response = await fetch('http://localhost:8000/api/v1/names/generate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        culture: 'dwarven',
        gender: 'masculine',
        count: 5
    })
});
const data = await response.json();
```

### cURL

```bash
curl -X POST "http://localhost:8000/api/v1/names/generate" \
     -H "Content-Type: application/json" \
     -d '{"culture":"human","count":10}'
```

## 🐛 Troubleshooting

### Common Issues

**Issue**: Names are too similar
- **Solution**: Adjust syllable patterns in culture templates
- **Solution**: Increase uniqueness scoring weight

**Issue**: Poor pronunciation scores
- **Solution**: Review phonotactic rules in `phonetics.py`
- **Solution**: Adjust culture-specific consonant/vowel sets

**Issue**: Slow generation for large batches
- **Solution**: Enable Redis caching
- **Solution**: Increase cache TTL for frequently used patterns

See [FAQ.md](docs/FAQ.md) for more troubleshooting tips.

## 📜 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Linguistic patterns inspired by real-world naming traditions
- Phonotactic rules based on linguistic research
- Fantasy culture templates influenced by established fictional works

## 📧 Contact

- **Issues**: [GitHub Issues](https://github.com/yourusername/name-generator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/name-generator/discussions)
- **Email**: your.email@example.com

---

**Built with ❤️ for storytellers, game developers, and world builders**