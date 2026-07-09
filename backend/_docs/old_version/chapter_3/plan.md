# Chapter 3: Bibliographic Research — Plan & Status

> **STATUS: IMPLEMENTED.** The `.tex` files are written and aligned with the
> already-implemented part of the thesis (Chapters 4 and 5). This chapter does not
> stand alone — it is deliberately structured to mirror the three analytical pillars
> that the system actually implements, so the literature gaps it identifies are exactly
> the gaps the implementation fills.

## Guiding principle: Chapter 3 must match the implementation

The implementation (Chapters 4–5) is built on three pillars. Chapter 3 reviews the
literature for each pillar and shows the open gap that HospitAI closes:

| Implemented pillar (Ch. 4/5) | Chapter 3 section | Gap exposed in the related work |
|---|---|---|
| K-Prototypes mixed-type clustering | §3.1 Patient Clustering | Prior algorithms are numeric-only; no automated interpretation |
| PrefixSpan, cluster-scoped, closed + gml + Jaccard | §3.2 Sequential Pattern Mining | Mining not conditioned on phenotype; no auto narrative |
| LLM verbaliser + guardrailed Text-to-SQL agent | §3.3 LLMs & Prompt Engineering | Prompt frameworks ignore structured ML output; no AST-validated SQL |
| End-to-end integration | §3.4 Comparative Analysis | No single framework unifies all pillars |

---

## File structure (mirrors Chapters 2/4/5 convention)

```
chapter_3/
├── bibliographic_research.tex   ← \chapter{Bibliographic Research}\label{ch:research} + opening + \input × 4
├── section_1.tex                ← \section{Patient Clustering and Phenotyping Methodologies}
├── section_2.tex                ← \section{Sequential Pattern Mining in Clinical Pathways}
├── section_3.tex                ← \section{Large Language Models and Prompt Engineering in Healthcare}
└── section_4.tex                ← \section{Comparative Analysis and Conclusions} (Table 3.1)
```

`\label{ch:research}` matches the forward reference already present in `chapter_1`.

---

## Papers reviewed (all in `_docs/articles/related_work/`, all in `thesis.bib`)

| Section | Paper | Cite key | Role |
|---|---|---|---|
| §3.1 | Aljohani (2024) — 8-algorithm clustering comparison via Fuzzy TOPSIS | `aljohani2024` | numeric-only limitation |
| §3.1 | Yang et al. (2024) — smart healthcare clustering system | `yang2024` | manual interpretation limitation |
| §3.1 | Najjar et al. (2018) — k-Prototypes + HMM pathway mining | `najjar2018` | closest prior work; bridges to §3.2 |
| §3.2 | Perer et al. (2015) — Care Pathway Explorer (visual analytics) | `perer2015` | no per-cluster scope, no auto narrative |
| §3.2 | Baudrier et al. (2022) — CP-SPAM + HCPC trajectory clustering | `baudrier2022` | no LLM interpretation, no re-ranking |
| §3.3 | Liu et al. (2025) — clinical prompt-engineering tutorial | `liu2025` | ignores structured ML output, no guardrailed SQL |

Background-only (not formally reviewed, available if more depth is needed): Vogt (2018),
Murazzano (2026), Rosa (2022), Flothow (2023).

---

## Per-paper formula applied (3 paragraphs each)
1. **What** — authors, year, problem.
2. **How** — technical approach (metrics, datasets, algorithm).
3. **Criticism** — gap vs. HospitAI, phrased to point at a concrete implemented feature
   (native mixed-type distance, per-cluster scoping, closed/gml/Jaccard re-ranking,
   AST-validated read-only SQL, deterministic verbaliser).

---

## Length
~2,160 body words + Table 3.1 + headings ≈ **5–6 pages** (target met).

---

## Checklist

- [x] `thesis.bib` entries added: aljohani2024, yang2024, najjar2018, perer2015, baudrier2022, liu2025
- [x] `\chapter` + `\label{ch:research}` + opening paragraph
- [x] §3.1 — Aljohani, Yang, Najjar (3-paragraph reviews)
- [x] §3.2 — Perer, Baudrier (3-paragraph reviews)
- [x] §3.3 — Liu (3-paragraph review + exact criticism text)
- [x] §3.4 — synthesis paragraph + Table 3.1 + closing
- [x] All `\cite{}` keys present in `thesis.bib`
- [x] Length within 3–10 pages (~5–6)
- [ ] Compile check once a `main.tex` exists (verify `\input` paths and Table 3.1 render)
