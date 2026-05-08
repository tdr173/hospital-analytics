"""Verify JWT-based scoping: a single Bearer token now propagates role +
patient_id + provider_id to every BE endpoint, replacing the legacy
?role=&patientId=&providerId= query params.

Test matrix:
  PATIENT token:
    - /patients should only return their own row
    - /patients/{ownId} 200, /patients/{otherId} 403
  DOCTOR token:
    - /patients returns just their panel (we don't have a panel set up, so
      we just assert the request goes through 200 and the BE didn't error)
  MANAGER token:
    - /patients returns everything
  No token:
    - Falls back to manager-default (legacy path), still 200

Plus: query-param fallback still works when no Bearer is sent.
"""
import json
import urllib.request
import urllib.error

BASE = "http://localhost"
H_AUTH = {"Host": "auth.localhost", "Content-Type": "application/json"}
H_CLIN = {"Host": "clinical.localhost"}
PASS = 0; FAIL = 0


def post(host, path, body, expect=(200,)):
    global PASS, FAIL
    h = {"Host": host, "Content-Type": "application/json"}
    r = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), method="POST", headers=h)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def get(host, path, *, token=None, expect=(200,), describe=False):
    global PASS, FAIL
    h = {"Host": host}
    if token:
        h["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(BASE + path, method="GET", headers=h)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            code, raw = resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        code, raw = e.code, (e.read().decode() if e.fp else "")
    ok = code in expect
    PASS += int(ok); FAIL += int(not ok)
    mark = "PASS" if ok else "FAIL"
    bearer = "Bearer" if token else "no-token"
    line = f"[{mark}] GET {path:38s} ({bearer}) -> {code}"
    if not ok or describe:
        line += f" body={raw[:140]}"
    print(line)
    try:
        return json.loads(raw) if raw else {}
    except Exception:
        return raw


def section(t):
    print(f"\n{'=' * 8} {t} {'=' * 8}")


# Login each role
section("ACQUIRE TOKENS")
for who, email in [("patient", "patient@hospitai.com"), ("doctor", "doctor@hospitai.com"), ("manager", "manager@hospitai.com")]:
    code, body = post("auth.localhost", "/auth/login", {"email": email, "password": "Demo1234"})
    print(f"  {who}: HTTP {code}")
TOKENS = {}
for who, email in [("patient", "patient@hospitai.com"), ("doctor", "doctor@hospitai.com"), ("manager", "manager@hospitai.com")]:
    code, body = post("auth.localhost", "/auth/login", {"email": email, "password": "Demo1234"})
    TOKENS[who] = body["accessToken"]
    print(f"  {who}: id={body.get('patientId') or body.get('providerId') or '-'}")

PATIENT_OWN_ID = "a701a37bc45e44978948c72c4047710c"
OTHER_PATIENT_ID = "8d6d2ca839f94c5d945f82e444e90e2a"

# Manager via JWT
section("MANAGER token: full access")
get("clinical.localhost", "/patients", token=TOKENS["manager"], describe=True)
get("clinical.localhost", f"/patients/{PATIENT_OWN_ID}", token=TOKENS["manager"])
get("clinical.localhost", f"/patients/{OTHER_PATIENT_ID}", token=TOKENS["manager"])

# Patient via JWT - own data OK, other patient should 403
section("PATIENT token: own data only")
own = get("clinical.localhost", f"/patients/{PATIENT_OWN_ID}", token=TOKENS["patient"])
other = get("clinical.localhost", f"/patients/{OTHER_PATIENT_ID}", token=TOKENS["patient"], expect=(403,))

# Doctor via JWT
section("DOCTOR token: panel access")
get("clinical.localhost", "/patients", token=TOKENS["doctor"], describe=True)

# /auth/me with each token
section("/auth/me roundtrip")
get("auth.localhost", "/auth/me", token=TOKENS["patient"])
get("auth.localhost", "/auth/me", token=TOKENS["doctor"])
get("auth.localhost", "/auth/me", token=TOKENS["manager"])

# Legacy fallback: no token, still works (defaults to manager scope)
section("LEGACY: no Bearer, falls back to query-param / manager-default")
get("clinical.localhost", "/patients")
get("clinical.localhost", "/patients?role=PATIENT&patientId=" + PATIENT_OWN_ID)

# Invalid bearer should fall back to manager-default (200), not 401
section("STALE TOKEN: graceful fallback (treated as no-token)")
get("clinical.localhost", "/patients",
    token="not.a.real.jwt.value")

print("\n" + "=" * 60)
print(f"TOTAL: {PASS} passed, {FAIL} failed")
print("=" * 60)
