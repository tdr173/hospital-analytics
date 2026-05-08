# Diagram sources

The 14 most-important diagrams from the thesis (`docs/thesis/chapters_4_5_6.md`) live here in source form, split by tool. Each `.txt` file is self-contained and can be rendered independently.

## Layout

```
docs/diagrams/
├── plantuml/   # UML diagrams: use case, deployment, ER, class, sequence, package
└── mermaid/    # flowcharts, state machines, architecture, mindmap-like graphs
```

## Files

| # | Path | Figure | Tool | What it shows |
|---|------|--------|------|---------------|
| 1 | `plantuml/01_use_case_diagram.txt` | 4.1 | PlantUML | PATIENT/DOCTOR/MANAGER actors and the use cases they reach |
| 2 | `plantuml/02_deployment_diagram.txt` | 5.2 | PlantUML | Docker host with every container, ports, Traefik routing |
| 3 | `plantuml/03_clinical_schema_er.txt` | 5.5 | PlantUML | Full ER diagram of `clinical-db` (12 tables) |
| 4 | `plantuml/04_login_sequence.txt` | 5.17 | PlantUML | JWT login (success + failure paths) |
| 5 | `plantuml/05_patient_created_fanout.txt` | 5.18b | PlantUML | `patient.created` → auth + mail-service async fan-out |
| 6 | `plantuml/06_cluster_run_sequence.txt` | 5.19 | PlantUML | Manager triggers k-Prototypes; ml-batch reads/writes |
| 7 | `plantuml/07_backend_package_diagram.txt` | 5.9 | PlantUML | Strict layered architecture (api → service → repository → domain) |
| 8 | `mermaid/01_system_architecture.txt` | 5.1 | Mermaid | Concrete Docker topology with all 16 containers |
| 9 | `mermaid/02_rabbitmq_topology.txt` | 5.25 | Mermaid | `clinical.events` topic exchange + 3 queues + bindings |
| 10 | `mermaid/03_llm_agent_state_graph.txt` | 4.25 | Mermaid | LangGraph state machine of the LLM SQL agent |
| 11 | `mermaid/04_etl_flowchart.txt` | 4.5 | Mermaid | Truncate → Load → Refresh MV phases |
| 12 | `mermaid/05_kprototypes_flowchart.txt` | 4.8 / 5.23 | Mermaid | `run_kprototypes` activity flow |
| 13 | `mermaid/06_prefix_span_pipeline.txt` | 4.19b / 4.24 | Mermaid | Sequence shaping → mining → ranking → dedup → attribution |
| 14 | `mermaid/07_bounded_context_map.txt` | 4.28 | Mermaid | The seven DDD bounded contexts and their conceptual links |

## Rendering

### PlantUML

Online: paste the `.txt` content into <https://www.plantuml.com/plantuml/uml/>.

CLI (requires Java + `plantuml.jar`):

```powershell
java -jar plantuml.jar -tpng docs/diagrams/plantuml/*.txt
java -jar plantuml.jar -tsvg docs/diagrams/plantuml/02_deployment_diagram.txt
```

VS Code: install the **PlantUML** extension, open a `.txt` file, `Alt+D` to preview.

### Mermaid

Online: paste the `.txt` content into <https://mermaid.live>.

CLI (Node):

```powershell
npm install -g @mermaid-js/mermaid-cli
mmdc -i docs/diagrams/mermaid/01_system_architecture.txt -o out.png
mmdc -i docs/diagrams/mermaid/01_system_architecture.txt -o out.svg
```

VS Code: install the **Mermaid Preview** extension, open a `.txt` file, run `Mermaid Preview` from the command palette.

GitHub renders Mermaid natively in `.md` files — wrap the contents in a ` ```mermaid ` code-fence to get a live preview in PR descriptions or markdown notes.

## Conventions

* All node/edge labels are in English (matching the thesis text). Comments at the top of each file are in English too — they are stripped by both renderers.
* The cluster colour palette used in cluster-aware diagrams matches the LLM-prompted production palette: `#DC2626` red, `#16A34A` green, `#2563EB` blue, `#D97706` orange, `#7C3AED` purple, `#0891B2` teal, `#9CA3AF` outliers.
* Sequence diagrams use **solid arrows for HTTP** (synchronous) and **dashed arrows for AMQP** (asynchronous). System-architecture flowcharts follow the same convention.
* When a figure is referenced in two chapters (e.g. ETL flowchart in 4.5 and 5.22), the source file is placed once and re-cited in both chapters.

## Adding more diagrams

The diagram inventory in `docs/thesis/chapters_4_5_6.md` (Appendix A and Appendix B) lists 117 figures + 6 listings. The 14 here are the highest-priority subset. To add a new one:

1. Pick the right tool (UML structure → PlantUML; flowchart/state/topology → Mermaid).
2. Add a numbered file `NN_short_name.txt` to the right folder.
3. Update the table above with the figure number and one-line description.
