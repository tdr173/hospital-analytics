# Structură Lucrare de Licență / Disertație
## HospitAI: A Hospital Analytics Platform Combining Patient Clustering, Clinical Sequence Mining and AI-Generated Interpretation

---

## Chapter 1 - Introduction
*Introducere în contextul analizei datelor medicale, importanța extragerii de traiectorii clinice și rolul inteligenței artificiale în interpretarea rezultatelor complexe.*

## Chapter 2 - Project Objectives
### 2.1 Main Objective

* **Design, implement, and test the HospitAI platform** to transform raw electronic health records (EHR) into actionable clinical insights. This core objective is achieved by engineering an end-to-end system that combines unsupervised patient stratification, sequential treatment pattern extraction, and automated statistical result interpretation through Large Language Models (LLMs).

### 2.2 Secondary Objectives

* **Study the state-of-the-art literature and existing algorithms:** Conduct a detailed analysis of current methodologies in Sequence Mining and LLMs to theoretically justify the architectural decisions, demonstrating the limitations of singular approaches in processing complex healthcare data.
* **Design the end-to-end data flow (ETL Pipeline) and database architecture:** Extract, transform, and load raw synthetic data into a relational database to filter noise, derive patient-level clinical features, and create a standardized environment essential for downstream machine learning tasks.
* **Implement the proposed methodology for patient stratification and clinical trajectory extraction:** Apply unsupervised learning algorithms to segment patients into homogeneous phenotypes handling mixed-type attributes, followed by pattern mining algorithms to discover frequent and relevant clinical sequences within the history of each specific cluster.
* **Develop an LLM-based conversational and decision-support interface:** Integrate an intelligent agent with a dual purpose: safely translating natural language queries into read-only SQL code to explore the database, and generating explicit, constraint-based clinical summaries of the discovered care pathways.
* **Rigorously test, validate, and evaluate the system outcomes:** Assess the quality of the proposed architecture using internal validation metrics for clustering and statistical measures for sequential patterns, while strictly verifying the safety and accuracy of the LLM-generated responses to prevent clinical hallucinations.

---

## Chapter 3 - Bibliographical Research
### 3.1 Clustering and sequence mining in the context of patient data
*Notă metodologică: Se va adopta un stil critic, dar respectuos relativ la metodele analizate în literatură, evidențiind limitările actuale pe care lucrarea își propune să le adreseze.*

#### 3.1.1 Patient Clustering Methodologies
* Analiza a **4 articole de referință** din domeniu.
* Tabel/secțiune de comparație detaliată per metodă (avantaje, dezavantaje, tipuri de date suportate).

#### 3.1.2 Sequential Pattern Mining Methods
* Analiza a **4 articole de referință** axate pe extragerea de tipare secvențiale din date clinice.
* Comparație analitică per metodă.

### 3.2 Large Language Models and Prompt Engineering in Health Care
* Analiza a **3 articole recente** privind utilizarea LLM-urilor în medicină și tehnici de structurare a prompt-urilor.
* Comparație critică între abordările identificate.

### 3.3 Conclusions
* Sintetizarea lipsurilor din literatura actuală și justificarea nevoii platformei HospitAI.

---

## Chapter 4 - Analysis and Theoretical Foundation
### 4.1 Analysis
#### 4.1.1 Use-Case Analysis
* Definirea actorilor principali ai sistemului (ex. personal medical, administratori de date) și a cazurilor de utilizare.

#### 4.1.2 Functional and Non-Functional Requirements
* *Atenție la Requirements:* Se vor păstra exclusiv cerințele deja realizate și complet realiste. Scopul central al lucrării nu este implementarea unei platforme web comerciale/complexe, ci crearea si validarea riguroasă a pipeline-ului analitic.

### 4.2 Theoretical Foundation
#### 4.2.1 Clustering Algorithms, Distances and Mixed-Type Data Handling
##### 4.2.1.1 Fundamentals of Clustering
* Ce reprezintă procesul de clustering, conceptul matematic de distanță/similaritate și mecanismul general de funcționare al unui algoritm de grupaj.
##### 4.2.1.2 Different Clustering Distances
* Analiza metricilor de distanță (Euclidiană, Manhattan, Gower, distanțe pentru variabile categorice precum Hamming etc.).
##### 4.2.1.3 Available Clustering Algorithms
* Trecere în revistă a algoritmilor existenți (K-Means, Hierarchical, DBSCAN), evidențierea diferențelor structurale și argumentarea aleerii algoritmului **K-Prototypes**.
##### 4.2.1.4 Mixed-Type Clustering and K-Prototypes
* Detalierea matematică a algoritmului K-Prototypes și a modului în care combină distanța Euclidiană cu similaritatea bazată pe coincidențe pentru date mixte (numerice + categorice).

#### 4.2.2 Sequential Patterns Mining
##### 4.2.2.1 Fundamentals of Sequence Mining
* Ce este Sequence Mining-ul, utilitatea sa în analiza evoluției pacienților și principiile fundamentale de funcționare.
##### 4.2.2.2 Available Sequence Mining Algorithms
* Analiza algoritmilor existenți (AprioriAll, GSP, SPADE, PrefixSpan). Comparație directă între aceștia și justificarea aleerii algoritmului **PrefixSpan** (eficiență computațională prin proiecția bazei de date).
##### 4.2.2.3 The PrefixSpan Algorithm
* Detalierea mecanismului de descompunere și proiecție recursivă specific PrefixSpan.

#### 4.2.3 AI-Driven Patient Phenotyping and Pathway Discovery
*(Titlul umbrelă pentru metodologia proprie) - Această secțiune grupează toate abstractizările matematice și conceptuale ale soluției, fără elemente de cod sau detalii de implementare hardware/software.*

##### 4.2.3.1 Formal Problem Definition
* Definirea matematică a problemei: modelarea pacientului ca un tuplu de caracteristici mixte și a istoricului său medical ca o secvență ordonată cronologic de evenimente clinice.
##### 4.2.3.2 Data Context and Validity
* Prezentarea conceptuală a setului de date. Mentionarea faptului că, pentru un volum mare de pacienți, acuratețea statistică și reprezentativitatea analizei converg către cea a datelor medicale oficiale.
##### 4.2.3.3 Conceptual Architecture of the Analytical Pipeline
* Diagrama de arhitectură logică și prezentarea soluției proprii pentru rezolvarea problemei de analiză integrată, totul păstrat la nivel conceptual.
##### 4.2.3.4 Bridging the Semantic Gap via Large Language Models
* Explicarea abstractă a modului în care LLM-ul traduce rezultatele matematice aride (clustere și tipare secvențiale) în narațiuni clinice ușor de înțeles. Concepte de interpretare automată și utilizarea unui Agent SQL conversational pentru a permite utilizatorilor non-tehnici să interogheze baza de date.

---

## Chapter 5 - System Design and Implementation
### 5.1 System Design
#### 5.1.1 System Architecture
* Arhitectura generală a platformei web care gestionează, orchestrează și expune utilizatorului final pipeline-ul analitic descris în secțiunea 4.2.3.3.
#### 5.1.2 Database Design
* Schema bazei de date relaționale: descrierea celor **11 tabele rezultate din procesul ETL** (Stage 1), alături de cele **5 tabele de legătură** utilizate direct în interfața grafică.
#### 5.1.3 Backend Design
* Diagrama de clase Python și descrierea la nivel înalt a structurii monolitice a backend-ului.
#### 5.1.4 Frontend Design
* Arhitectura aplicației construite în Next.js, incluzând structura paginilor, rutele principale și fluxul utilizatorului.

### 5.2 System Implementation
#### 5.2.1 Frontend Implementation
* Detalii privind implementarea componentelor de interfață în Next.js/React, vizualizarea grafică a clusterelor și a traiectoriilor, interfața de chat cu agentul și managementul stării.

#### 5.2.2 Backend Implementation
* Secțiune-umbrelă care grupează toate componentele implementate pe partea de backend (BE). Fiecare subsecțiune de mai jos detaliază câte un modul al pipeline-ului analitic.

##### 5.2.2.1 ETL Pipeline
* Transpunerea în cod a procesului de Extract, Transform, Load: curățarea datelor primare, maparea structurilor medicale și popularea celor 11 tabele din baza de date.

##### 5.2.2.2 K-Prototypes Clustering
* Generarea setului de caracteristici (feature engineering), curățarea valorilor aberante (outliers), generarea automată a graficului Elbow (Elbow Plot) și mecanismul de trimitere a clusterelor rezultate către interpretarea automată.

##### 5.2.2.3 PrefixSpan Customizations
* Detalierea și explicarea celor **6 îmbunătățiri/optimizări aduse algoritmului clasic PrefixSpan** pentru a se plia eficient pe specificul datelor clinice din platformă.

##### 5.2.2.4 Pipeline Orchestration
* Implementarea jobului Python cu rulare lunară (cron/worker) dedicat re-antrenării și actualizării modelelor, incluzând și opțiunea de declanșare manuală din panoul de administrare.

##### 5.2.2.5 AI Results Generation
* Structura și ingineria prompt-urilor utilizate pentru interpretarea clusterelor și a secvențelor, definirea schemelor stricte pentru *expected input* și *expected output* (JSON enforcement).

##### 5.2.2.6 LLM SQL Agent (LangGraph)
* Arhitectura internă a agentului conversațional SQL, utilizarea framework-ului LangGraph pentru controlul stării și definirea grafului direct orientat (DAG) ce guvernează deciziile agentului în timpul interogării.

---

## Chapter 6 - Testing and Validation
### 6.1 Used Dataset
* Prezentarea practică și empirică a setului de date utilizat în rulări (volum, distribuție, statistici descriptive).
### 6.2 K-Prototypes Metrics
* Fundamentele teoretice ale metricilor folosite pentru evaluarea calității clustering-ului pe date mixte (ex. Cost function/Inertia, Average Silhouette Width adaptat sau scoruri de stabilitate).
### 6.3 K-Prototypes Results
* Analiza rezultatelor în urma testării a **60 de configurații distincte** de hyperparametri de-a lungul a **629 de rulări**. Explicarea modului în care s-a calculat un scor empiric compozit în funcție de metrici, alegându-se pentru interpretarea finală cele mai bune configurații pentru **k=4, k=5 și k=6**.
### 6.4 Sequence Mining Metrics
* Definirea teoretică și practică a metricilor specifice analizei de tipare secvențiale (Support, Confidence, Lift adaptat secvențelor sau lungimea medie a secvențelor relevante).
### 6.5 Sequence Mining Results
* Evaluarea și interpretarea empirică a rezultatelor extrase. Validarea calitativă: analiza demonstrează că printre rezultatele per cluster nu există niciun tipar secvențial extras care să nu fie clinic relevant pentru patologia sau specificul clusterului din care face parte.
