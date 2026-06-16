# CSSC 2026 — HospitAI paper

IEEE conference paper (6–8 pages, English) for the Computer Science Students
Conference 2026.

- **Conference:** June 26, 2026
- **Submission deadline:** June 18, 2026, end of day
- **Submit PDF + registration form to:** paulina.mitrea@cs.utcluj.ro
- **Format:** IEEE (`IEEEtran`, `conference` mode)

## How to compile

### Option A — Overleaf (recommended, no install)
1. Create a new project, upload this whole `cssc2026/` folder.
2. Set the main document to `main.tex`. Overleaf ships `IEEEtran` — it just works.
3. Compile (pdfLaTeX). Overleaf runs BibTeX automatically.

### Option B — local
Install a TeX distribution (MiKTeX on Windows / TeX Live), then:
```
pdflatex main
bibtex main
pdflatex main
pdflatex main
```
If `IEEEtran.cls` is missing, download it from the conference template or
CTAN and drop it next to `main.tex`.

## File layout (one file per section — "latex per chapter")
```
main.tex                       preamble, title, author, \input order
refs.bib                       references (BibTeX)
sections/abstract.tex
sections/intro.tex             I.   Introduction + contributions
sections/related.tex           II.  Related Work
sections/overview.tex          III. System Overview (+ architecture figure)
sections/methods_ingestion.tex IV-A Data Ingestion & Feature Building
sections/methods_clustering.tex IV-B Mixed-Type Clustering (K-Prototypes)
sections/methods_sequences.tex IV-C Dual-Scope PrefixSpan  <-- main contribution
sections/methods_llm.tex       IV-D LLM Interpretation Layer
sections/results.tex           V.   Results & Evaluation
sections/discussion.tex        VI.  Discussion & Limitations
sections/conclusion.tex        VII. Conclusion & Future Work
figures/                       put exported figures here (see below)
```

## Before submitting — checklist
- [ ] Fill author name + email in `main.tex`; add coordinating professor if required.
- [ ] Replace every `\TODO{...}` (shown in red). Search the project: `grep -rn TODO sections`.
- [ ] **Metrics table** (`results.tex`): paste real silhouette / Davies–Bouldin /
      Calinski–Harabasz values from the clustering evaluation report / `cluster_meta.metrics`.
- [ ] **Patterns table** (`results.tex`): paste 2–3 real per-cluster vs global
      trajectories with support % from the `prefix_span_pattern` tables.
- [ ] **Figures** in `figures/`:
      - architecture diagram (adapt the PlantUML in `backend/app/docs/chapter_5/`)
      - FAMD scatter (export from `cluster_meta.pca_image`)
      - optionally the cluster heatmap
      Then swap the `\fbox{...}` placeholders for `\includegraphics`.
- [ ] Confirm page count is 6–8 after figures/tables are in. Trim Related Work
      or Discussion first if over.
- [ ] Verify `\NPATIENTS` (currently 22,284) and `\KCLUSTERS` (currently 4) match
      the run you report.
