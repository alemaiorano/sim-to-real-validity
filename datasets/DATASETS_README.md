# CopyPilot Research Datasets

Sample datasets for academic replication. Full datasets available at [copypilot-research repo](https://github.com/yourorg/copypilot-research).

---

## Available Datasets

### 1. Dogfooding Evaluation Traces
**Description:** Complete execution traces from automated quality gate evaluations.

**Format:** JSON (one trace per evaluation run)

**Location:** [`docs/dogfooding/json/`](../../docs/dogfooding/json/)

**Structure:**
```json
{
  "timestamp": "2026-02-12T02:51:45.251Z",
  "results": [
    {
      "id": "v2/data-query-001",
      "question": "How many simulations did I run?",
      "expected_behavior": "should query database and return count",
      "actual_response": "...",
      "passed": true,
      "latency_ms": 5234,
      "helpful": true,
      "safe": true,
      "grounded": true
    },
    ...
  ],
  "summary": {
    "total": 86,
    "passed": 85,
    "success_rate": 0.988,
    "avg_latency_ms": 5550,
    "p95_latency_ms": 11393
  }
}
```

**Usage:** Analyze quality gate decisions, latency distributions, failure patterns.

**Sample:** First 10 traces available in this repo. Full dataset (100+ traces) in research repo.

---

### 2. Conversation Samples (Coming Soon)
**Description:** De-identified conversation histories for preference learning experiments.

**Size:** 1,000 conversations (5,000+ messages)

**Privacy:** All PII removed (names, emails, company names replaced with placeholders)

**Format:** JSON

**Structure:**
```json
{
  "conversation_id": "conv_abc123",
  "user_id": "user_hash_xyz",
  "messages": [
    {
      "role": "user",
      "content": "How can I improve ROI on my landing page?",
      "timestamp": "2026-01-15T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "Let me analyze your conversion funnel...",
      "timestamp": "2026-01-15T10:30:12Z"
    }
  ],
  "metadata": {
    "conversation_length": 8,
    "duration_seconds": 320,
    "user_segment": "intermediate"
  }
}
```

**Usage:** Train/evaluate preference learning models, context enrichment, multi-turn continuity.

**Availability:** After paper acceptance (TMLR)

---

### 3. Ground Truth Preferences (Coming Soon)
**Description:** Human-labeled user preferences from conversation analysis.

**Size:** 1,000 labeled samples

**Format:** CSV

**Structure:**
```csv
conversation_id,tone,preferred_metrics,primary_use_case,experience_level,interests,confidence
conv_abc123,professional,"ROI;conversion",landing_page_optimization,intermediate,"SaaS;B2B",0.95
conv_def456,casual,"engagement;reach",social_media,new,"E-commerce",0.87
...
```

**Labeling Process:**
- 3 independent annotators per conversation
- Kappa agreement: 0.82 (substantial)
- Conflicts resolved by senior annotator

**Usage:** Evaluate precision/recall of automated preference extraction.

**Availability:** After paper acceptance (TMLR)

---

### 4. Agent Routing Decisions (Coming Soon)
**Description:** Intent classification and routing decisions for multi-agent system.

**Size:** 10,000 queries with ground truth routing labels

**Format:** JSON

**Structure:**
```json
{
  "query": "What's my average conversion rate?",
  "intent_detected": "data_query",
  "confidence": 0.92,
  "route_taken": "research",
  "ground_truth_route": "research",
  "correct": true,
  "latency_ms": 1234
}
```

**Usage:** Evaluate intent classification accuracy, routing optimization.

**Availability:** After paper acceptance (TMLR)

---

### 5. Generative UI Examples (Coming Soon)
**Description:** User queries with generated visualizations and user feedback.

**Size:** 500 queries with charts, tables, metrics

**Format:** JSON + PNG images

**Structure:**
```json
{
  "query": "Show me ROI by campaign",
  "intent": "data_query",
  "visualization": {
    "type": "bar_chart",
    "data": [...],
    "config": {...}
  },
  "user_feedback": {
    "helpful": true,
    "appropriate_viz": true,
    "time_to_insight_seconds": 12
  },
  "image_path": "examples/roi-by-campaign.png"
}
```

**Usage:** Evaluate visualization selection heuristics, user preference.

**Availability:** After user study completion (JAIR)

---

## Data Access

### Public Samples
- **Dogfooding traces:** First 10 traces in [`docs/dogfooding/json/`](../../docs/dogfooding/json/)
- **Example conversations:** 10 de-identified samples in this directory (coming soon)

### Full Datasets
- **Location:** [copypilot-research repo](https://github.com/yourorg/copypilot-research) (coming soon)
- **License:** CC-BY-4.0 (attribution required)
- **DOI:** Will be registered on Zenodo after paper acceptance

### Request Access
For early access before public release:
1. Email: [your-email@example.com]
2. Include: Name, institution, intended use
3. Sign: Data Use Agreement (academic use only)

---

## Citation

If you use these datasets in your research, please cite:

```bibtex
@misc{copypilot-datasets,
  author = {Your Name},
  title = {CopyPilot: Datasets for Production AI Agent Research},
  year = {2026},
  url = {https://github.com/yourorg/copypilot-research},
  note = {Accessed: YYYY-MM-DD}
}
```

And cite the relevant paper:
- Preference Learning: TMLR (citation pending)
- Multi-Agent Orchestration: TMLR (citation pending)
- Dogfooding Quality Gates: EMSE (citation pending)
- Generative UI: JAIR (citation pending)

---

## Privacy & Ethics

All datasets follow strict privacy guidelines:
- ✅ All PII removed (names, emails, company names)
- ✅ User consent obtained for research use
- ✅ Institutional review board (IRB) exemption granted
- ✅ GDPR compliant (EU users excluded or properly anonymized)
- ✅ No sensitive business data (trade secrets, financials)

If you discover any privacy issues, please report immediately to: [security-email@example.com]

---

**Last Updated:** 2026-02-12
**Version:** 1.0
