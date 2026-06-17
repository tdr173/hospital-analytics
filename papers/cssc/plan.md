# CSSC 2026 Paper Plan -- "HospitAI"

## Target venue
- **CSSC 2026 Student Conference** (Technical University of Cluj-Napoca).
- **Format:** IEEE conference format, two columns (`IEEEtran`, option `conference`).
- **Length:** 6 to 8 pages, including references.
- **Language:** English.
- **Submission:** PDF + Registration Form, by 18 June 2026.

## Scope and tone
- High-level overview of the whole platform. We explain *what* each part does and *why*, and we keep the algorithm details readable.
- B2-level English: short to medium sentences, common vocabulary, no rare or "fancy" words.
- No em-dashes anywhere. Use commas, parentheses, or split the sentence.
- Write in a natural, slightly varied style (first person plural, "we built", "we found"). Avoid template phrases.

## Files (one per chapter)
| File | Section | Purpose |
|------|---------|---------|
| `main.tex` | preamble + includes | document class, packages, title, abstract, includes |
| `01_introduction.tex` | I. Introduction | problem, motivation, contributions |
| `02_related_work.tex` | II. Related Work | the 9 useful papers, grouped |
| `03_system_overview.tex` | III. System Overview | architecture, data (Synthea), tech stack |
| `04_methodology.tex` | IV. Methods | clustering, sequence mining, AI interpretation |
| `05_results.tex` | V. Results | clustering metrics, the v0->v6 story, sequence examples |
| `06_conclusion.tex` | VI. Discussion and Conclusion | limitations, future work, summary |
| `references.bib` | bibliography | shared with MediTech |

## Chapter outline

### I. Introduction
- Hospitals store large EHR data but rarely turn it into clear pictures of patient groups and care paths.
- Three problems: (1) patients are heterogeneous, (2) care unfolds over time as sequences of events, (3) raw model output is hard for non-experts to read.
- HospitAI answers these with K-Prototypes clustering, a domain-adapted PrefixSpan pipeline, and an LLM that turns numbers into plain language.
- Contributions list (4 bullets).

### II. Related Work
- Surveys of patient-pathway mining: rosa2022modelling, flothow2023.
- Combined clustering + sequence mining: najjar2018twostep (k-prototypes + pathways), baudrier2022, vogt2017.
- Sequence mining from EMR with interpretation: perer2015mining.
- Clustering of patients on EHR / mixed data: yang2024, aljohani2024.
- Process mining alternative: murazzano2026.
- Gap we fill: one integrated tool that scopes mining by cluster, ranks patterns for clinical usefulness, and adds an LLM verbalizer.

### III. System Overview
- Layered architecture: Next.js frontend -> FastAPI (api / service / repository / domain) -> PostgreSQL.
- Two offline ML scripts (clustering, mining) write results back into the DB; the web app reads them.
- Data: Synthea synthetic EHR, ~22,284 patients, tables for encounters, conditions, medications, procedures, observations, careplans.
- Single LLM (OpenAI GPT) for all text generation.

### IV. Methods
- 4.A Feature engineering (raw tables -> 5 numerical + 8 categorical features; log1p, binning with "Unknown", no one-hot).
- 4.B K-Prototypes clustering (Huang's mixed-data method; gamma; minmax scaling; z-score outliers kept as cluster -1; k chosen by elbow + Gower silhouette).
- 4.C Sequence mining (events typed C/M/P/CP; one sequence per patient; same-day order; PrefixSpan base; GML ranking; type-diversity bonus; diversification caps; full-spectrum quota; per-cluster scope + cross-scope dedup).
- 4.D AI interpretation (LLM as a verbalizer over fixed statistics; cluster cards, sequence summaries; guarded NL-to-SQL agent with LangGraph).

### V. Results
- Clustering: k=4 final pick, Gower 0.350, per-cluster silhouettes, 4 readable cohorts.
- Sequence mining: the v0 (rank by support, dental flooding) vs v6 (rank by GML, clinical chains) contrast. Use Table with example patterns.
- Outlier scope surfacing oncology/renal/heart-failure pathways.

### VI. Discussion and Conclusion
- What works, honest limitations (synthetic data, no clinical validation, single LLM, qualitative pattern quality).
- Future work (real data, expert evaluation, gap constraints).

## Figures and tables
1. **Fig. 1 -- Architecture** (TikZ, self-contained): frontend -> backend layers -> DB, plus offline ML scripts and LLM.
2. **Fig. 2 -- Sequence-mining pipeline** (TikZ): raw events -> typed sequences -> PrefixSpan -> GML scoring -> diversification -> per-scope patterns -> LLM.
3. **Fig. 3 -- Cluster heatmap** (`figs/cluster_heatmap.png`, real result): z-scored numerical means per cluster.
4. **Fig. 4 -- Categorical panel** (`figs/cluster_categorical.png`, real result): optional, drop if over length.
5. **Table I -- Clustering winners** per k (from chapter 6 results).
6. **Table II -- Example mined pathways** (the v6 / per-cluster top patterns).
7. **Table III -- v0 vs v6 ablation** (trivial vs clinical top pattern).

## Citation note
- All domain citations come from the `useful` folder (9 papers).
- Two extra references (Huang 1998, Pei et al. 2004) are the original algorithm papers. They are mandatory method-origin citations and are not domain papers, so they are kept separate in the .bib.
