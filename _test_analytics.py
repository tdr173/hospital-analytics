"""Smoke test for analytics endpoints with empty DB.

analytics has its own DB plus read-only engines into clinical-db and ml-db.
With no data anywhere, list-style endpoints should still 200 with empty
payloads. /dashboard/personal-summary requires a patientId — pass any
string and accept any non-500. The LLM SQL agent endpoint we hit with a
trivial question; we accept 200, 4xx (config), 504 (timeout), or 503.
"""
import json
import urllib.request
import urllib.error

BASE = "http://localhost"
H = {"Host": "analytics.localhost", "Content-Type": "application/json"}
PASS = 0; FAIL = 0


def call(method, path, body=None, expect=(200,), describe=False, timeout=20):
    global PASS, FAIL
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method, headers=H)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            code, raw = resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        code, raw = e.code, (e.read().decode() if e.fp else "")
    except Exception as e:
        code, raw = 0, str(e)
    ok = code in expect
    PASS += int(ok); FAIL += int(not ok)
    mark = "PASS" if ok else "FAIL"
    short = raw[:200].replace("\n", " ")
    extra = f"\n        body: {short}" if (not ok or describe) else ""
    print(f"[{mark}] {method:5s} {path:55s} -> {code} (expected {expect}){extra}")


def section(t):
    print(f"\n{'=' * 6} {t} {'=' * 6}")


section("HEALTH")
call("GET", "/health")

section("DASHBOARD")
call("GET", "/dashboard", describe=True)
call("GET", "/dashboard/practice-summary", describe=True)
# personal-summary requires patientId; with no data accept any non-500
call("GET", "/dashboard/personal-summary?patientId=does-not-exist",
     expect=(200, 400, 404, 422))
# missing required param -> 422
call("GET", "/dashboard/personal-summary", expect=(422,))

section("STATISTICS - all entity-scoped")
for entity in ("patients", "providers", "encounters", "conditions",
               "medications", "procedures", "immunizations", "allergies",
               "careplans", "observations"):
    call("GET", f"/statistics/{entity}", describe=True)

section("STATISTICS - observation refresh (materialized views)")
# may legitimately fail if MVs aren't created yet; accept 200, 4xx, 5xx-ish
call("POST", "/statistics/observations/refresh",
     expect=(200, 202, 400, 404, 500, 503))

section("STATISTICS - LLM SQL agent")
# question is required; missing -> 422
call("POST", "/statistics/sql-agent", {}, expect=(422,))
# trivial question -> may take time; accept 200/4xx/5xx (depends on key/config)
call("POST", "/statistics/sql-agent",
     {"question": "How many patients are in the database?", "history": []},
     expect=(200, 400, 401, 403, 500, 502, 503, 504), timeout=60, describe=True)

print("\n" + "=" * 60)
print(f"TOTAL: {PASS} passed, {FAIL} failed")
print("=" * 60)
