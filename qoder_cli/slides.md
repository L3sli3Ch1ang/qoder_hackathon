---
marp: true
theme: default
paginate: true
style: |
  * {
    background: transparent;
  }
  section {
    background-color: #0f172a;
    color: #f8fafc;
    font-family: Inter, system-ui, -apple-system, sans-serif;
  }
  h1, h2, h3, h4, h5, h6 {
    color: #06b6d4;
    background: transparent;
  }
  p, li, ul, ol {
    color: #94a3b8;
    background: transparent;
  }
  strong, b {
    color: #f8fafc;
  }
  a {
    color: #06b6d4;
    background: transparent;
  }
  table {
    background: transparent;
    border-collapse: collapse;
    width: 100%;
  }
  th {
    background-color: #1e293b;
    color: #06b6d4;
    border: 1px solid #334155;
    padding: 8px 12px;
  }
  td {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    padding: 8px 12px;
  }
  code {
    background-color: #1e293b;
    color: #10b981;
    padding: 2px 6px;
    border-radius: 3px;
  }
  pre {
    background-color: #1e293b;
    padding: 12px;
    border-radius: 6px;
  }
  pre code {
    background-color: transparent;
    color: #f8fafc;
  }
  blockquote {
    background-color: #1e293b;
    border-left: 4px solid #06b6d4;
    padding: 8px 16px;
    color: #94a3b8;
  }
  section.small-table table {
    font-size: 14px;
  }
  section.small-table th,
  section.small-table td {
    padding: 4px 8px;
  }
---

# SkillBridge SG

## Cross-Sector Skills Matching for Singapore's Workforce

**"Making every transferable skill count"**

Alibaba Cloud × Qoder Hackathon Singapore 2026

---

# The Problem

Singapore's SkillsFuture actively encourages **cross-sector career mobility**, yet existing job platforms fail to support it:

- **LinkedIn, MyCareersFuture, JobStreet** use single-sector keyword matching
- A professional accountant with "Data Analytics + Python" is **invisible** to AI Governance roles in ICT — and vice-versa
- Binary skill matching (has / doesn't have) ignores **proficiency levels**
- No lightweight tool understands transferable skills across sectors

---

# Success Metrics

| Objective | Demonstration |
|---|---|
| Ranked results in < 1 second | Live app + latency tests |
| Proficiency-aware scoring (PL 1-6) | matched_detail per result |
| Cross-sector bridge visible | Bridge chips + confidence |
| Every recommendation traceable | Data provenance |
| Inspectable & reproducible | 97-test suite + deterministic seed |

---

# What SkillBridge Does

Paste a Job Description → ranked, explained results in **< 1 second**

- Understands **transferable skills** across sectors
- **Proficiency-aware scoring** (PL 1-6, partial credit)
- Every result is **explainable** (matched, gaps, bridges, courses)
- Accessible to recruiters and career coaches without a data-science team

---

# The 8-Stage Pipeline (Core Effort)

```
JD → BM25 (top-50) → Dense (top-50) → RRF Fusion (top-30) → 
     Cross-Encoder (top-10) → Explainability → Surprise → 
     Narrative → Courses
```

**Why hybrid?** Lexical (BM25) catches exact keywords but misses semantic similarity. Dense embeddings catch transferable skills but can drift off-topic. **Reciprocal Rank Fusion** merges both robustly, and a **cross-encoder** scores each (JD, candidate) pair for precise ranking.

**Funnel**: 150 candidates → 50+50 recalled → 30 fused → 10 re-ranked → scored & explained

---

# Proficiency-Aware Scoring (Differentiator)

Official SWDA proficiency scale:
**1 Use → 2 Operate → 3 Apply → 4 Implement → 5 Analyse → 6 Assess/Lead**

**Per-skill credit**:
- Full credit `1.0` if candidate_PL ≥ required_PL
- Partial credit `candidate_PL / required_PL` if below required level
- Zero if skill is absent

**Hybrid display score**: `40 + 58 × (0.3 × semantic_norm + 0.7 × proficiency_fit)` → range 40-98

70% weight on proficiency fit ensures **real skill match dominates text similarity**

---

# Bridge Skills (Transferable Evidence)

A bridge answers: *"Candidate lacks skill X, but has skill Y — how much of X is covered by Y?"*

**Derived from 150K+ Knowledge & Ability (K&A) items** in the official SWDA dataset

Containment score: `|S ∩ V| / |S|`, floor 0.2, Critical Core Skills (CCS) +0.1 boost

**53 evidence-based bridges** with explicit confidence scores (0.20-0.87)

---

<!-- _class: small-table -->

# Data Provenance (Not a Black Box)

All data grounded in **official SWDA Skills Framework dataset**:

| Seed File | Count | Key Details |
|---|---|---|
| jobs.json | 30 roles | 6 × 5 sectors, skill_requirements verbatim |
| candidates.json | 150 profiles | Anchored to real roles, ~78% skill coverage |
| skill_registry.json | 434 skills | TSC/CCS titles, Emerging/CASL flags |
| skill_taxonomy.json | 5 sectors | finance 70, ict 63, healthcare 80, eng 64, sustainability 77 |
| bridges.json | 53 bridges | K&A containment, floor 0.2, CCS +0.1 boost |
| courses.json | 434 entries | Live MySkillsFuture search URLs |

**Deterministic**: `random.seed(20260729)` → byte-identical output, auditable, validated

---

# What It Can Do

✅ Match JD → ranked results in < 1 second  
✅ Proficiency-aware scoring (PL 1-6) grounded in official data  
✅ Cross-sector bridge skills with evidence-backed confidence  
✅ Explainability panel: matched, gaps, bridges, courses  
✅ What-if explorer: add/remove skills, see scores shift ▲/▼  
✅ Hire ↔ Upskill perspective toggle  
✅ Surprise mode: surface serendipitous candidates  
✅ Emerging & CASL badges from official dataset  
✅ Sector convergence strip (Jaccard overlap visualization)  
✅ 97 tests, fully reproducible, deterministic  

**Cannot**: production-scale talent pool, real resume parsing, open-ended NLP skill extraction  

---

# Demo

**Video**: https://youtu.be/DhmpkfX31yg

**GitHub**: https://github.com/L3sli3Ch1ang/qoder_hackathon.git

Live app: FastAPI + Alpine.js + Tailwind

Run locally:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

---

# Built with Qoder

**Quest Mode**: spec + scaffold, SWDA data integration, 6-phase development

**Expert Mode**: 8-stage pipeline, proficiency scoring, bridge derivation from 150K+ K&A items

**qodercli**: test runs, isolated worktree, `/review`, `/init`

**2 weeks**, 97 tests, real government data, deterministic seed generation

Evidence: `AGENTS.md`, `docs/evidence/`, `docs/evidence/code-reviews/`

**Stack**: FastAPI + Alpine.js + Tailwind, sentence-transformers, Qdrant Lite, DashScope qwen-plus, NixOS + direnv

---

# Roadmap

**Future investments (in priority order):**

1. **Real candidate ingestion** — parse PDF/DOCX resumes, map to SWDA taxonomy
2. **Scale corpus** — expand from 5 to 38 SWDA sectors (2,030 roles / 12,007 skills)
3. **Richer skill extraction** — NER/embedding-based detection beyond taxonomy
4. **Live data sync** — periodic re-derivation from SWDA/MySkillsFuture releases
5. **Persistence & accounts** — save searches, track pipelines, multi-user
6. **Outcome feedback loop** — tune blend weights based on actual hires
7. **Bias & fairness review** — audit scorer for sector/seniority bias

---

# Thank You

Questions?

**Demo**: https://youtu.be/DhmpkfX31yg  
**GitHub**: https://github.com/L3sli3Ch1ang/qoder_hackathon.git

#QoderHackathon #BuildWithQoder #SkillsFuture #AlibabaCloud
