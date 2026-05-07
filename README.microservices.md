# Hospital Analytics — Microservices Deployment

7 backend services + 1 frontend, each in its own container, routed by **Traefik** (host-based). Data ownership is enforced by **per-service Postgres** instances. Cross-service state is kept coherent by **RabbitMQ** events, not cross-DB joins.

## Topology

| Service | Host | Routers | Owns DB |
|---|---|---|---|
| `frontend` | http://app.localhost | Next.js | — |
| `auth` | http://auth.localhost | `/auth/*` | `auth-db` (`auth_user`) |
| `users` | http://users.localhost | (placeholder) | reads `auth-db` |
| `clinical-core` | http://clinical.localhost | `/patients/*`, `/providers/*`, `/encounters/*` | `clinical-db` (patient, provider, encounter, condition, medication, allergy, careplan, observation, immunization, procedure, organization, patient_provider) + materialized views |
| `analytics` | http://analytics.localhost | `/statistics/*`, `/dashboard/*` | `analytics-db` + read connections to `clinical-db`, `ml-db` |
| `ml-batch` | http://ml.localhost | `/clusters/*`, `/sequences/*` | `ml-db` (cluster, cluster_meta, cluster_patient, prefix_span_*) + read connection to `clinical-db` |
| `mail-service` | http://mail.localhost | (RabbitMQ consumer) | — |
| `queue-service` | http://queue.localhost | (placeholder) | `queue-db` |
| Traefik dashboard | http://localhost:8090 | | |
| RabbitMQ UI | http://localhost:15672 | guest/guest | |

## Repo layout

```
hospital-analytics/
├── docker-compose.yml         # builds each service from its own folder
├── traefik/traefik.yml
├── frontend/                  # Next.js (own Dockerfile)
└── services/
    ├── auth/                  # Dockerfile, requirements.txt, app/
    ├── users/
    ├── clinical-core/
    ├── analytics/
    ├── ml-batch/
    ├── mail-service/
    └── queue-service/
```

Each service is **self-contained**: own Dockerfile, own `requirements.txt` (only the libs that service needs — heavy ML deps are confined to `ml-batch`), and its own copy of `app/`. Services pick which routers to expose via the `SERVICE_NAME` env var (set in compose).

## How table ownership is enforced

`services/<svc>/app/db/model_registry.py` maps `SERVICE_NAME` → set of tables. At startup, `SQLModel.metadata.create_all(engine, tables=...)` runs only the subset this service owns. Cross-DB foreign keys (`auth_user.patient_id`, `cluster_patient.patient_id`) were dropped from the models — referential integrity now lives at the application layer + sync events.

## Cross-service sync (RabbitMQ)

All events go through one topic exchange `clinical.events` with routing keys `<entity>.<action>`.

| Event | Publisher | Subscriber | Effect |
|---|---|---|---|
| `patient.created` (with `email`) | clinical-core | auth | provisions PATIENT account, sends invite email |
| `patient.deleted` | clinical-core | auth | deletes linked auth account |
| `patient.deleted` | clinical-core | ml-batch | deletes orphaned `cluster_patient` rows in `ml-db` |
| `provider.created` (with `email`) | clinical-core | auth | provisions DOCTOR account |
| `provider.deleted` | clinical-core | auth | deletes linked auth account |
| `encounter.created/updated/deleted` | clinical-core | (open) | analytics view-refresh hook later |
| `notification.send` | any | mail-service | sends transactional email |

Consumer code lives in each service's own folder, e.g. `services/auth/app/sync/account_consumer.py`. Each starts as an asyncio task in its service's lifespan.

## Read replicas (the analytics + LLM SQL agent path)

`analytics` needs to query data that lives in `clinical-db` and `ml-db`. We do not duplicate that data; instead, each container gets read-only connection strings to the other DBs:

```
analytics container env:
  POSTGRES_*       -> analytics-db   (primary, writable)
  CLINICAL_DB_*    -> clinical-db    (read engine)
  ML_DB_*          -> ml-db          (read engine)
```

`db.db_connector.read_engine("clinical")` returns the SQLAlchemy engine. The LLM SQL agent uses this read connection — it cannot write.

## Run it

1. Copy env files:
   ```powershell
   Copy-Item .env.example .env
   Copy-Item frontend\.env.example frontend\.env.local
   ```
   Fill `SECRET_KEY`, `GEMINI_API_KEY`, `GPT_KEY`.

2. `C:\Windows\System32\drivers\etc\hosts`:
   ```
   127.0.0.1 app.localhost auth.localhost users.localhost clinical.localhost analytics.localhost ml.localhost mail.localhost queue.localhost
   ```

3. Boot:
   ```powershell
   docker compose up --build
   ```

4. Open http://app.localhost.

## Frontend wiring

`frontend/utils/apiBases.ts` exports `apiUrl(path)` which routes by path prefix to the correct service base. Every `thunks.ts` calls `apiUrl("/...")`. Override per-service URLs via `NEXT_PUBLIC_*_URL`.

## Caveats

- **`*.localhost` browser support.** Chrome resolves any `*.localhost` host to 127.0.0.1 automatically. Firefox/Safari may not — add the entries to `C:\Windows\System32\drivers\etc\hosts` (see step 2 above) to be safe.
- **`clinical-db` exposes 5432 on the host.** Useful for ETL scripts but conflicts with any local Postgres on 5432. Comment out the `ports:` block in `docker-compose.yml` if that's a problem, or before deploying to production.
- **FE env vars are build-time, not runtime.** `NEXT_PUBLIC_*` URLs are baked into the JS bundle by `npm run build`. They're passed via `build.args` in `docker-compose.yml`. Changing them at runtime has no effect — you must rebuild the frontend image (`docker compose build frontend`) for changes to apply.
- **Each service folder is a full code copy.** A code change to a shared module (e.g. `messaging/`, `_security.py`) must be applied in every `services/<svc>/app/` folder until per-service code pruning is done. Consider using a top-level shared package or git submodule when the duplication starts to bite.

## Future work

- **Prune per-service `app/` trees.** Each `services/<svc>/app/` is a full copy of the original codebase — it works because the per-service `SERVICE_NAME` env tells `main.py` which routers to register and which migrations to run. A follow-up pass can delete unused routers/services/repos from each folder so they only carry the code they actually run.
- Replace query-param scope (`role=`, `patientId=`) with JWT claims.
- Wire APScheduler in `queue-service` for nightly recluster.
- Production: Traefik + Let's Encrypt.
- ETL: `db/etl_script.py` currently expects a single Postgres — point it at `clinical-db` (port 5432 exposed on host) and add a separate ml-loader at `ml-db`.
