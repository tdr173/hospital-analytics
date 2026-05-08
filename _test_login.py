"""Verify the 3 seeded accounts can log in via real /auth/login.

Covers:
  - Successful login for each role; assert response shape (role, IDs, JWT)
  - JWT works against /auth/me
  - Wrong password -> 401 with clear message
  - Missing field / malformed email -> 422
  - Unknown email -> 401 with same generic message (anti-enumeration)
"""
import json
import urllib.request
import urllib.error

BASE = "http://localhost"
H = {"Host": "auth.localhost", "Content-Type": "application/json"}

PASS = 0
FAIL = 0


def req(method, path, body=None, headers=None, expect=(200,)):
    global PASS, FAIL
    h = headers or H
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            code, raw = resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        code, raw = e.code, (e.read().decode() if e.fp else "")
    except Exception as e:
        code, raw = 0, str(e)
    ok = code in expect
    PASS += int(ok); FAIL += int(not ok)
    mark = "PASS" if ok else "FAIL"
    line = f"[{mark}] {method:6s} {path:25s} -> {code} (expected {expect})"
    if not ok:
        line += f"\n        body: {raw[:200]}"
    print(line)
    try:
        return json.loads(raw) if raw else {}
    except Exception:
        return raw


def assert_eq(label, got, expected):
    global PASS, FAIL
    ok = got == expected
    PASS += int(ok); FAIL += int(not ok)
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {label}: got {got!r}, expected {expected!r}")


def section(t):
    print(f"\n{'=' * 8} {t} {'=' * 8}")


# ---------- HAPPY PATH FOR EACH ROLE ----------
section("LOGIN: 3 seeded accounts")

PATIENT = req("POST", "/auth/login",
    {"email": "patient@hospitai.com", "password": "Demo1234"})
assert_eq("patient role", PATIENT.get("role"), "PATIENT")
assert_eq("patient must_change_password", PATIENT.get("mustChangePassword"), False)
ok = bool(PATIENT.get("patientId")) and not PATIENT.get("providerId")
PASS += int(ok); FAIL += int(not ok)
print(f"[{'PASS' if ok else 'FAIL'}] patient has patientId, no providerId")
patient_token = PATIENT.get("accessToken")

DOCTOR = req("POST", "/auth/login",
    {"email": "doctor@hospitai.com", "password": "Demo1234"})
assert_eq("doctor role", DOCTOR.get("role"), "DOCTOR")
ok = bool(DOCTOR.get("providerId")) and not DOCTOR.get("patientId")
PASS += int(ok); FAIL += int(not ok)
print(f"[{'PASS' if ok else 'FAIL'}] doctor has providerId, no patientId")
doctor_token = DOCTOR.get("accessToken")

MANAGER = req("POST", "/auth/login",
    {"email": "manager@hospitai.com", "password": "Demo1234"})
assert_eq("manager role", MANAGER.get("role"), "MANAGER")
ok = not MANAGER.get("patientId") and not MANAGER.get("providerId")
PASS += int(ok); FAIL += int(not ok)
print(f"[{'PASS' if ok else 'FAIL'}] manager has neither patient nor provider id")
manager_token = MANAGER.get("accessToken")

# ---------- /auth/me with each token ----------
section("GET /auth/me with each JWT")
for label, tok in [("patient", patient_token), ("doctor", doctor_token), ("manager", manager_token)]:
    me = req("GET", "/auth/me",
        headers={**H, "Authorization": f"Bearer {tok}"})
    print(f"  {label}: email={me.get('email')} role={me.get('role')}")

# ---------- ERROR CASES ----------
section("ERRORS: wrong creds + validation + unknown email")
# wrong password -> 401 + clear message
err = req("POST", "/auth/login",
    {"email": "patient@hospitai.com", "password": "wrong-password"},
    expect=(401,))
assert_eq("wrong-pwd detail", err.get("detail"), "Invalid email or password")

# unknown email -> 401 with same message (anti-enum)
err = req("POST", "/auth/login",
    {"email": "ghost@hospitai.com", "password": "anything-long-enough"},
    expect=(401,))
assert_eq("unknown-email detail", err.get("detail"), "Invalid email or password")

# missing password -> 422
req("POST", "/auth/login", {"email": "patient@hospitai.com"}, expect=(422,))

# missing email -> 422
req("POST", "/auth/login", {"password": "Demo1234"}, expect=(422,))

# malformed email -> 422
req("POST", "/auth/login",
    {"email": "not-an-email", "password": "Demo1234"},
    expect=(422,))

print("\n" + "=" * 60)
print(f"TOTAL: {PASS} passed, {FAIL} failed")
print("=" * 60)
