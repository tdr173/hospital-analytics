# Plan de finalizare — Lucrare de licență HospitAI

> Plan derivat din analiza comparativă cu lucrarea model (Varga Zoltan) și **verificat față de starea reală a fișierelor din repo**.
> Convenție: lucrarea e scrisă în LaTeX, împărțită pe fișiere (`_docs/` + `app/docs/`). Orice capitol nou se redactează în **același stil** (`\section` / `\subsection` / `\subsubsection*`).

---

## 1. Starea reală a lucrării (verificată în fișiere)

Fiecare capitol e acum împărțit pe fișiere în `_docs/chapter_N/` (main `\chapter` +
`section_*.tex`, iar secțiunile cu subsecțiuni au subfoldere `section_N/` cu `N.S.x.tex`).

| Capitol | Folder | Stare |
|---|---|---|
| 1. Introduction | `_docs/chapter_1/introduction.tex` | Schelet scurt — fără secțiuni (de extins opțional) |
| 2. Objectives | `_docs/chapter_2/` (section_1, section_2) | OK, împărțit |
| 3. Bibliographic Research | `_docs/chapter_3/` (bibliographic_research + section_1..4) | **GATA** (~5–6 pagini) |
| 4. Analysis & Theoretical Foundation | `_docs/chapter_4/` (section_1/, section_2/) | Foarte complet, împărțit |
| 5. Detailed Design & Implementation | `_docs/chapter_5/` (section_1/, section_2/) | Aproape complet, împărțit |
| 6. Testing & Validation | `_docs/chapter_6/` (section_1/) | Parțial, împărțit |
| 7. User's Manual | — | **LIPSEȘTE** |
| 8. Conclusions | — | **LIPSEȘTE** |

Bibliografie: `_docs/thesis.bib` — extinsă la **19 intrări** (cele 6 noi pentru Cap. 3 adăugate).

---

## 2. Corecții față de analiza primită (ce este deja făcut)

Analiza externă este parțial **depășită**. Înainte de a rescrie ceva, ține cont:

1. **Metricile de evaluare NU lipsesc.** `_docs/analysis.tex` conține deja subsecțiunea
   *Mixed-Type Clustering Validation Metrics* cu **6 metrici + formule**:
   Silhouette, Gower Silhouette, Calinski-Harabasz, Davies-Bouldin, Cramér's V, Eta².
   → În Cap. 6 **NU le rescriem**; doar le **referențiem** (`\ref`/`Section 4.x`).

2. **Cap. 5 are deja arhitectură + deployment implicit.** `design_implementation.tex`
   acoperă: General Architecture, Traefik, microservicii (Auth/Users/Analytics/Clinical
   Core/Queue/Mail), Frontend Architecture, ETL, K-Prototypes, PrefixSpan, LLM SQL Agent.
   → Singurul gol structural real în Cap. 5 este **Database Design (diagrama ER)**.

3. **Sequence mining metrics** (support, lift, closedness, Jaccard) sunt deja definite
   în `analysis.tex` (subsecțiunea PrefixSpan). → idem, doar referențiere în Cap. 6.

---

## 3. Goluri reale de acoperit

- ~~**Cap. 3** — Bibliographic Research~~ → **GATA** (6 lucrări recenzate, Tabel 3.1, `.bib` extins).
- **Cap. 5** — subsecțiune **Database Design** (diagramă ER din modelele reale).
- **Cap. 6** — subsecțiuni **Dataset** și **Configuration parameters** (cifre reale din cod/DB).
- **Cap. 7** — User's Manual (Deployment + Usage guide).
- **Cap. 8** — Conclusions (Contributions / Result analysis / Further development).
- **Cap. 1** — extindere introducere (opțional, e scurtă).

---

## 4. Plan de execuție (ordine recomandată)

### Pas 1 — Cap. 3: Bibliographic Research
- Selectează **5–7 lucrări** relevante: clustering pe date medicale mixte + sequential
  pattern mining pe istoricul pacienților + Text-to-SQL/LLM pe date clinice.
- Pentru fiecare: problemă abordată, algoritm (ex. K-Means, GSP, SPADE, SQLNet), limitări.
- **Tabel comparativ** (ca Table 3.1 din model): coloane *Reference | Objective | Algorithms
  | Limitations*, cu **HospitAI ca rând final** pentru a evidenția avantajul.
- Extinde `_docs/thesis.bib` cu intrările noi (de la 13 → ~20–25).
- *Input necesar de la tine:* confirmarea lucrărilor de citat (sau le propun eu și le validezi).

### Pas 2 — Cap. 5: Database Design (subsecțiune nouă)
- Generez **diagrama ER** din sursa reală: modelele SQLModel din `domain/models` +
  tabelele `cluster_meta`, `cluster`, `cluster_patient`, `prefix_span_pattern`.
- Tabele cheie: patients, encounters, conditions, medications, observations, procedures
  + tabelele de analiză (clustering / pattern mining).
- Descriu relațiile many-to-many și coloanele computate (deja menționate în ETL).
- *Ancorat 100% în cod — fără input extern.*

### Pas 3 — Cap. 6: Dataset + Configuration (subsecțiuni noi, ÎNAINTE de rezultate)
- **6.x Dataset:** statistici reale despre datele Synthea (nr. pacienți, distribuție
  vârstă/sex, nr. encounters/conditions/observations procesate) — extrase din DB / `etl_script.py`.
- **6.x Configuration parameters:** K (nr. clustere), nr. iterații, init Huang/Cao, γ,
  pragul de suport σ pentru PrefixSpan, praguri Jaccard/lift — extrase din `k_prototypes.py`
  și pipeline-ul PrefixSpan.
- Metricile rămân **referențiate** din Cap. 4 (vezi §2).

### Pas 4 — Cap. 7: User's Manual
- **7.1 Deployment:** pași reali pe mașină locală (instalare dependențe, `.env`, pornire
  PostgreSQL, `uvicorn app.main:app --reload`, `npm run dev`, eventual Docker/Traefik).
- **7.2 Usage guide:** flux principal cu capturi de ecran:
  - *Doctor* → accesează un pacient, vede clusterul alocat și cardurile AI.
  - *Manager* → folosește agentul LLM Text-to-SQL pentru interogări în limbaj natural.
- *Input necesar de la tine:* capturile de ecran din aplicație.

### Pas 5 — Cap. 8: Conclusions
- **8.1 Contributions:** integrare clustering mixt + pattern mining + interpretare LLM +
  conversie NL→SQL sigură.
- **8.2 Result analysis:** discuție critică despre limitările pe date Synthea (sintetice)
  și eficiența modelelor.
- **8.3 Further Development:** conectare la EHR reale, securitate date, optimizare batch/real-time.

### Pas 6 (opțional) — Cap. 1: extindere introducere

---

## 5. Surse din cod pe care le folosesc (pentru a nu inventa date)

- `domain/models`, `domain/schemas` → schema DB / diagrama ER.
- `db/etl_script.py` → sursa Synthea, ordinea de ingestie, coloane computate, statistici dataset.
- `clustering_algorithms/k_prototypes/k_prototypes.py` + `save_results.py` → parametri K-Prototypes.
- pipeline PrefixSpan → parametri sequence mining (σ, lift, Jaccard).
- `service/lllm_sql_agent_service/` → descriere agent Text-to-SQL pentru Cap. 7.
- `app/main.py` → migrații / coloane (`ai_analysis`, `pca_image`) pentru Database Design.

---

## 6. Decizii de luat (deschise)

- [ ] Lista finală de lucrări pentru Cap. 3 (le propun eu sau le dai tu?).
- [ ] Profunzime redactare: draft complet vs. schelet (de stabilit per capitol).
- [ ] Capturi de ecran pentru Cap. 7 (le faci tu din aplicația rulată).
- [ ] Limba lucrării: engleză (toate fișierele existente sunt în engleză) — se păstrează.

---

## 7. Stare plan

- [x] Pas 1 — Cap. 3 Bibliographic Research (scris, aliniat cu implementarea)
- [ ] Pas 2 — Cap. 5 Database Design
- [ ] Pas 3 — Cap. 6 Dataset + Configuration
- [ ] Pas 4 — Cap. 7 User's Manual
- [ ] Pas 5 — Cap. 8 Conclusions
- [ ] Pas 6 — Cap. 1 (opțional)
