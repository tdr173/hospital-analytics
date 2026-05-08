"""End-to-end smoke test for clinical-core service via Traefik."""
import json
import urllib.request
import urllib.error
import sys
import os

BASE = "http://localhost"
HOST = "clinical.localhost"
HEADERS = {"Host": HOST, "Content-Type": "application/json"}

PASS = 0
FAIL = 0
RESULTS = []


def req(method, path, body=None, expect=(200,)):
    global PASS, FAIL
    url = BASE + path
    data = None
    if body is not None:
        data = json.dumps(body).encode()
    r = urllib.request.Request(url, data=data, method=method, headers=HEADERS)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            code = resp.status
            raw = resp.read().decode()
    except urllib.error.HTTPError as e:
        code = e.code
        raw = e.read().decode() if e.fp else ""
    except Exception as e:
        code = 0
        raw = str(e)
    ok = code in expect
    PASS += 1 if ok else 0
    FAIL += 0 if ok else 1
    short = raw[:200].replace("\n", " ")
    mark = "PASS" if ok else "FAIL"
    line = f"[{mark}] {method:6s} {path:55s} -> {code} (expected {expect})"
    if not ok:
        line += f"\n        body: {short}"
    RESULTS.append(line)
    print(line)
    if not ok:
        return None
    try:
        return json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        return raw


def section(title):
    print(f"\n{'=' * 6} {title} {'=' * 6}")


# ---------- HEALTH + RESOURCES ----------
section("HEALTH & RESOURCES")
req("GET", "/health")
req("GET", "/patients/resources")
req("GET", "/providers/resources")
req("GET", "/encounters/resources")

# ---------- LIST (empty) ----------
section("LIST (empty)")
req("GET", "/patients")
req("GET", "/providers")
req("GET", "/encounters")

# ---------- CREATE PROVIDER ----------
section("PROVIDER LIFECYCLE")
prov = req("POST", "/providers", {
    "firstName": "Dr. Test",
    "lastName": "Smoke",
    "gender": "M",
    "speciality": "GENERAL PRACTICE",
    "city": "Test City",
    "email": "dr.smoke@test.local",
}, expect=(200, 201))
PROVIDER_ID = (prov or {}).get("providerId") or (prov or {}).get("id")
print(f"   -> PROVIDER_ID={PROVIDER_ID}")

req("GET", f"/providers/{PROVIDER_ID}")
req("PATCH", f"/providers/{PROVIDER_ID}", {"city": "New Test City"})
req("GET", f"/providers/{PROVIDER_ID}/encounters")

# ---------- CREATE PATIENT ----------
section("PATIENT LIFECYCLE")
pat = req("POST", "/patients", {
    "firstName": "Smoke",
    "lastName": "Test",
    "age": 42,
    "birthdate": "1983-04-15",
    "gender": "F",
    "race": "white",
    "ethnicity": "nonhispanic",
    "marital": "M",
    "city": "Test City",
    "email": "smoke.test@test.local",
}, expect=(200, 201))
PATIENT_ID = (pat or {}).get("patientId") or (pat or {}).get("id")
print(f"   -> PATIENT_ID={PATIENT_ID}")

req("GET", f"/patients/{PATIENT_ID}")
req("PATCH", f"/patients/{PATIENT_ID}", {"city": "Another City"})
req("GET", f"/patients/{PATIENT_ID}/summary")
req("GET", f"/patients/{PATIENT_ID}/sequences")
req("GET", f"/patients/{PATIENT_ID}/sequence-continuations")

# ---------- CREATE ENCOUNTER ----------
section("ENCOUNTER LIFECYCLE")
enc = req("POST", "/encounters", {
    "patientId": PATIENT_ID,
    "providerId": PROVIDER_ID,
    "startDate": "2024-06-01T10:00:00",
    "endDate": "2024-06-01T11:00:00",
    "encounterClass": "ambulatory",
    "description": "Smoke test encounter",
    "reasonDescription": "Test reason",
}, expect=(200, 201))
ENC_ID = (enc or {}).get("encounterId") or (enc or {}).get("id")
print(f"   -> ENC_ID={ENC_ID}")

req("GET", f"/encounters/{ENC_ID}")
req("PATCH", f"/encounters/{ENC_ID}", {"description": "Updated encounter"})
req("GET", f"/patients/{PATIENT_ID}/encounters")
req("GET", f"/providers/{PROVIDER_ID}/encounters")

# ---------- ENCOUNTER CHILDREN: CREATE + LIST + PATCH ----------
section("ENCOUNTER CHILD RESOURCES")

children = {
    "allergies": {
        "create": {"startDate": "2024-06-01", "allergyCode": "300916003", "description": "Test allergy"},
        "patch": {"description": "Updated allergy"},
    },
    "careplans": {
        "create": {"startDate": "2024-06-01T10:00:00", "careplanCode": "326051000000105", "description": "Test careplan"},
        "patch": {"description": "Updated careplan"},
    },
    "conditions": {
        "create": {"startDate": "2024-06-01T10:00:00", "conditionCode": "44054006", "description": "Test condition"},
        "patch": {"description": "Updated condition"},
    },
    "immunizations": {
        "create": {"date": "2024-06-01T10:00:00", "immunizationCode": "140", "description": "Test immunization"},
        "patch": {"description": "Updated immunization"},
    },
    "medications": {
        "create": {"startDate": "2024-06-01T10:00:00", "medicationCode": "1000128", "description": "Test medication"},
        "patch": {"description": "Updated medication"},
    },
    "observations": {
        "create": {"date": "2024-06-01T10:00:00", "observationCode": "8480-6", "description": "Systolic BP", "value": "120", "valueNumeric": 120.0, "units": "mmHg"},
        "patch": {"value": "125"},
    },
    "procedures": {
        "create": {"startDate": "2024-06-01T10:00:00", "procedureCode": "23426006", "description": "Test procedure"},
        "patch": {"description": "Updated procedure"},
    },
}

CHILD_IDS = {}
for kind, spec in children.items():
    print(f"\n--- {kind} ---")
    created = req("POST", f"/encounters/{ENC_ID}/{kind}", spec["create"], expect=(200, 201))
    cid = None
    if isinstance(created, dict):
        for key in ("id", "recordId", f"{kind[:-1]}Id"):
            if key in created:
                cid = created[key]
                break
    CHILD_IDS[kind] = cid
    print(f"   -> {kind[:-1]}_id = {cid}")
    req("GET", f"/encounters/{ENC_ID}/{kind}")
    req("GET", f"/patients/{PATIENT_ID}/{kind}")
    if cid is not None:
        req("PATCH", f"/encounters/{ENC_ID}/{kind}/{cid}", spec["patch"])

# ---------- DELETE CHILDREN ----------
section("DELETE CHILD RESOURCES")
for kind, cid in CHILD_IDS.items():
    if cid is not None:
        req("DELETE", f"/encounters/{ENC_ID}/{kind}/{cid}", expect=(200, 204))

# ---------- DELETE ENCOUNTER, PATIENT, PROVIDER ----------
section("DELETE ENCOUNTER / PATIENT / PROVIDER (should publish events)")
req("DELETE", f"/encounters/{ENC_ID}", expect=(200, 204))
req("DELETE", f"/patients/{PATIENT_ID}", expect=(200, 204))
req("DELETE", f"/providers/{PROVIDER_ID}", expect=(200, 204))

# ---------- SUMMARY ----------
print("\n" + "=" * 60)
print(f"TOTAL: {PASS} passed, {FAIL} failed")
print("=" * 60)
sys.exit(0 if FAIL == 0 else 1)
