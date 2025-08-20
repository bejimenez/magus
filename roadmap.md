# Magus Development Roadmap

## Architecture Analysis
Proposed hybrid architecture smartly combines deterministic linguistic rules with ML flexibility. The key insight is that names need both structure (phonotactics, morphology) and creativity (style, cultural blending). This phased approach will build incrementally while maintaining testability.

## Development Phases

### **Phase 1: MVP - Rule-Based Foundation** (Weeks 1-3)
**Goal**: Create a working API that generates pronounceable names using basic patterns

**Features**:
- Simple syllable-based generation (CV, CVC, VC patterns)
- Basic name templates per culture/style (e.g., "Elvish" = soft consonants + vowel endings)
- REST API with basic parameters (culture, gender, length)
- Pronunciation scoring using simple phonotactic rules

**Technical Implementation**:
```
Input: {culture: "elvish", gender: "feminine", length: "medium"}
Process: Template selection → Syllable generation → Combination
Output: {name: "Lyralei", pronunciation: "lee-rah-lay", score: 0.85}
```

**Testing Strategy**:
- Unit tests for syllable generation
- Pronunciation validation against English phonotactics
- API integration tests
- Manual review of 100 generated names per culture

**Deliverable**: Working API that generates decent fantasy names for 3-5 cultures

---

### **Phase 2: Phoneme-Based Enhancement** (Weeks 4-6)
**Goal**: Replace syllable templates with proper phoneme sequences

**Features**:
- IPA-based phoneme representation
- Phonotactic constraint engine (culture-specific valid sequences)
- Improved pronunciation scoring
- Stress pattern generation

**Research Topics**:
- Study phonotactic patterns in target languages
- Implement Markov chains for phoneme transitions
- Research sonority sequencing principles

**Technical Implementation**:
```
Phoneme sequence: /l/ + /i/ + /r/ + /a/ + /l/ + /eɪ/
Constraints: No initial /ŋ/, vowel harmony rules
Stress: Primary on second syllable
```

**Testing**:
- Validate against real language phonotactic rules
- A/B test against Phase 1 output
- Linguistic expert review

---

### **Phase 3: Morphological Components** (Weeks 7-10)
**Goal**: Add meaningful name construction from roots and affixes

**Features**:
- Root/prefix/suffix database with meanings
- Morphological rules engine (compound formation, affixation)
- Semantic request parsing ("name meaning 'moonlight'")
- Etymology tracking

**Research Topics**:
- Study name etymology in target cultures
- Implement morphophonological rules (sound changes at morpheme boundaries)
- Research productive affixes in various naming traditions

**Technical Implementation**:
```
Request: "moonlight"
Morphemes: {luna: "moon", -iel: "light/radiance"}
Rules: Vowel harmony, liaison rules
Output: "Luniel" with etymology data
```

**Testing**:
- Semantic accuracy validation
- Morphological rule consistency
- User studies on perceived meaningfulness

---

### **Phase 4: Cultural Data Integration** (Weeks 11-13)
**Goal**: Enrich with real cultural patterns and metadata

**Features**:
- Cultural name database (10k+ names per culture with metadata)
- Statistical modeling of cultural patterns
- Gender/class/era associations
- Name frequency distributions

**Data Collection**:
- Public name databases (Behind the Name, government records)
- Fantasy literature corpus analysis
- Historical name records

**Technical Implementation**:
```
Cultural Profile: {
  phonemes: weighted_distribution,
  morphemes: frequency_map,
  patterns: n-gram_model,
  constraints: rule_set
}
```

---

### **Phase 5: Neural Fine-Tuning Layer** (Weeks 14-18)
**Goal**: Add ML creativity while maintaining linguistic validity

**Features**:
- Train small transformer model on name-culture pairs
- Style transfer capabilities ("make it more elegant")
- Cultural blending ("70% Japanese, 30% Celtic")
- Novelty generation with controlled randomness

**Research Topics**:
- Fine-tune small LLM (e.g., GPT-2 size) on name corpus
- Implement constrained decoding with phonotactic rules
- Study VAE approaches for name generation

**Technical Implementation**:
```
Base Generation → Neural Enhancement → Constraint Validation → Output
```

**Testing**:
- Compare neural vs rule-based quality
- Measure creativity/novelty scores
- Validate constraint adherence

---

### **Phase 6: Advanced Constraint System** (Weeks 19-21)
**Goal**: Handle complex multi-constraint requests

**Features**:
- Constraint satisfaction solver for complex requirements
- Soft vs hard constraint handling
- Requirement priority weighting
- Conflict resolution strategies

**Example Handling**:
```
Request: "Short but majestic, easy to pronounce, masculine, 
         Viking-inspired but with subtle Roman influence"
Constraints: length<=6, majesty_score>0.8, pronunciation<0.5,
            culture_blend={viking:0.7, roman:0.3}
```

---

### **Phase 7: Quality Metrics & Feedback Loop** (Weeks 22-24)
**Goal**: Implement comprehensive quality assessment and learning

**Features**:
- Multi-dimensional quality scoring
- User preference learning system
- A/B testing framework
- Feedback incorporation pipeline

**Metrics Implementation**:
- Pronounceability (phonotactic probability)
- Authenticity (cultural similarity score)
- Uniqueness (edit distance from existing names)
- Semantic coherence (embedding similarity)
- User satisfaction (implicit/explicit feedback)

---

### **Phase 8: Production Optimization** (Weeks 25-26)
**Goal**: Scale for production use

**Features**:
- Response time optimization (<100ms)
- Caching strategies
- Batch generation support
- Rate limiting and quota management
- Monitoring and analytics

---

## Research Priority Schedule

### Immediate Research (Before Phase 2):
- Phonotactic patterns in 5 target languages
- IPA transcription systems
- Basic Markov chain implementations

### Medium-term Research (Before Phase 5):
- Transformer architectures for structured generation
- Constrained decoding techniques
- VAE/GAN approaches for name generation

### Long-term Research (Ongoing):
- Cross-linguistic naming patterns
- Historical name evolution
- Sociolinguistic factors in naming

## Success Metrics by Phase

| Phase | Success Criteria | Measurement |
|-------|-----------------|-------------|
| 1 | 80% pronounceable names | Phonotactic scoring |
| 2 | 90% valid phoneme sequences | Linguistic validation |
| 3 | 70% semantic accuracy | User interpretation tests |
| 4 | 85% cultural authenticity | Expert evaluation |
| 5 | 2x creativity score increase | Novelty metrics |
| 6 | 95% constraint satisfaction | Automated validation |
| 7 | 4.0+ user satisfaction | User ratings |
| 8 | <100ms response time | Performance monitoring |

## Risk Mitigation

**Technical Risks**:
- Neural model overfitting → Use regularization, diverse training data
- Constraint conflicts → Implement priority system, soft constraints
- Performance bottlenecks → Profile early, optimize critical paths

**Quality Risks**:
- Cultural insensitivity → Expert review, diverse test groups
- Unpronounceable outputs → Strict phonotactic validation
- Repetitive generation → Novelty scoring, diversity penalties

## Recommended Tech Stack

**Backend**:
- Python (FastAPI for API)
- PostgreSQL (name database)
- Redis (caching)
- PyTorch/TensorFlow (neural components)

**Linguistic Libraries**:
- NLTK/spaCy (NLP processing)
- epitran (IPA conversion)
- panphon (phonological features)

**Testing**:
- pytest (unit/integration tests)
- Locust (load testing)
- MLflow (ML experiment tracking)

## Next Immediate Steps

1. **Week 1**: Set up API framework and basic syllable generator
2. **Week 2**: Implement 3 culture templates (e.g., Elvish, Dwarven, Human)
3. **Week 3**: Add pronunciation scoring and API documentation
4. **Week 4**: Begin phoneme research and IPA integration

This roadmap provides a clear path from simple rule-based generation to sophisticated ML-enhanced creation, with testable milestones at each phase.