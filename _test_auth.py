"""End-to-end auth service test.

Auth has only 4 endpoints:
  POST /auth/login
  GET  /auth/me
  POST /auth/set-password
  GET  /health

Account creation happens via RabbitMQ when clinical-core publishes
patient.created or provider.created. There is no /register endpoint.

There is no /logout endpoint either: tokens are stateless JWTs, so logout
is client-side only (discard the token). We assert that here.

Password reset = the initial set-password flow (after invite, an account
has must_change_password=True and a random temp password). The temp
password is bcrypt-hashed at creation, so we cannot read it back; instead
we overwrite it with a known hash via docker exec to drive the flow.
"""
import json
import subprocess
import time
import urllib.request
import urllib.error

BASE = "http://localhost"
AUTH = {"Host": "auth.localhost", "Content-Type": "application/json"}
CLIN = {"Host": "clinical.localhost", "Content-Type": "application/json"}
PASS = 0
FAIL = 0


def req(method, path, body=None, headers=None, expect=(200,)):
    global PASS, FAIL
    h = headers or AUTH
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
    line = f"[{mark}] {method:6s} {path:35s} -> {code} (expected {expect})"
    if not ok:
        line += f"\n        body: {raw[:200]}"
    print(line)
    try:
        return json.loads(raw) if raw else {}
    except Exception:
        return raw


def section(t):
    print(f"\n{'=' * 8} {t} {'=' * 8}")


def sql_clinical(q):
    subprocess.run(["docker", "exec", "hospital_clinical_db", "psql", "-U", "postgres", "-d", "clinical", "-c", q], check=True, capture_output=True)


def sql_auth(q):
    return subprocess.run(["docker", "exec", "hospital_auth_db", "psql", "-U", "postgres", "-d", "auth", "-At", "-c", q], capture_output=True, text=True, check=True).stdout.strip()


def bcrypt_hash(plain):
    out = subprocess.run(
        ["docker", "exec", "hospital_auth", "python", "-c",
         f"import bcrypt;print(bcrypt.hashpw(b'{plain}', bcrypt.gensalt()).decode())"],
        capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


# ---------- PHASE 1: Health ----------
section("HEALTH")
req("GET", "/health")

# Reset auth-db to a known state
print("\n[setup] TRUNCATE auth_user")
sql_auth("TRUNCATE auth_user RESTART IDENTITY;")

# ---------- PHASE 2: Sign-up flow via RabbitMQ (no /register endpoint) ----------
section("INVITE / PROVISIONING (RabbitMQ flow)")
PATIENT_EMAIL = "alice.invite@test.com"
PROVIDER_EMAIL = "dr.invite@test.com"

pat = req("POST", "/patients", {
    "firstName": "Alice", "lastName": "Invite", "age": 30,
    "birthdate": "1995-01-01", "gender": "F", "email": PATIENT_EMAIL,
}, headers=CLIN, expect=(201,))
PATIENT_ID = pat.get("patientId")

prov = req("POST", "/providers", {
    "firstName": "Dr", "lastName": "Invite",
    "speciality": "GP", "email": PROVIDER_EMAIL,
}, headers=CLIN, expect=(201,))
PROVIDER_ID = prov.get("providerId")

print("[setup] waiting for RabbitMQ consumer to provision both accounts...")
for _ in range(20):
    if sql_auth("SELECT count(*) FROM auth_user;") == "2":
        break
    time.sleep(0.5)
count = sql_auth("SELECT count(*) FROM auth_user;")
print(f"[check] auth_user rows after invite: {count} (expected 2)")
PASS += int(count == "2"); FAIL += int(count != "2")

row = sql_auth(
    f"SELECT email||'|'||role||'|'||must_change_password||'|'||COALESCE(patient_id,'')||'|'||COALESCE(provider_id,'') "
    f"FROM auth_user WHERE email='{PATIENT_EMAIL}';"
)
print(f"[check] patient row: {row}")
ok = (PATIENT_EMAIL in row) and ("PATIENT" in row) and ("|true|" in row)
PASS += int(ok); FAIL += int(not ok)

row = sql_auth(
    f"SELECT email||'|'||role||'|'||must_change_password||'|'||COALESCE(patient_id,'')||'|'||COALESCE(provider_id,'') "
    f"FROM auth_user WHERE email='{PROVIDER_EMAIL}';"
)
print(f"[check] provider row: {row}")
ok = (PROVIDER_EMAIL in row) and ("DOCTOR" in row) and ("|true|" in row)
PASS += int(ok); FAIL += int(not ok)

# ---------- PHASE 3: Patch known temp passwords ----------
section("PATCH KNOWN TEMP PASSWORDS")
TEMP_PWD = "TempPass123"
NEW_PWD = "NewPass456"
print(f"[setup] generating bcrypt hash for '{TEMP_PWD}'...")
hashed = bcrypt_hash(TEMP_PWD)
sql_auth(f"UPDATE auth_user SET password='{hashed}' WHERE email='{PATIENT_EMAIL}' OR email='{PROVIDER_EMAIL}';")
print("[setup] hashes patched")

# ---------- PHASE 4: SET-PASSWORD validation + happy path ----------
section("SET-PASSWORD FLOW")
# wrong temp pwd -> 400 (anti-enum: same message as user not found)
req("POST", "/auth/set-password",
    {"email": PATIENT_EMAIL, "temp_password": "wrong", "new_password": NEW_PWD},
    expect=(400,))
# unknown user -> 400
req("POST", "/auth/set-password",
    {"email": "ghost@nope.com", "temp_password": TEMP_PWD, "new_password": NEW_PWD},
    expect=(400,))
# new == temp -> 400
req("POST", "/auth/set-password",
    {"email": PATIENT_EMAIL, "temp_password": TEMP_PWD, "new_password": TEMP_PWD},
    expect=(400,))
# happy path -> 200
req("POST", "/auth/set-password",
    {"email": PATIENT_EMAIL, "temp_password": TEMP_PWD, "new_password": NEW_PWD},
    expect=(200,))
# replay -> 400 (must_change_password is now False)
req("POST", "/auth/set-password",
    {"email": PATIENT_EMAIL, "temp_password": TEMP_PWD, "new_password": NEW_PWD},
    expect=(400,))

# ---------- PHASE 5: LOGIN ----------
section("LOGIN")
req("POST", "/auth/login",
    {"email": PATIENT_EMAIL, "password": "wrong"},
    expect=(401,))
req("POST", "/auth/login",
    {"email": "ghost@nope.com", "password": NEW_PWD},
    expect=(401,))
patient_login = req("POST", "/auth/login",
    {"email": PATIENT_EMAIL, "password": NEW_PWD},
    expect=(200,))
PATIENT_TOKEN = patient_login.get("accessToken") if isinstance(patient_login, dict) else None
print(f"  patient role={patient_login.get('role')} must_change_password={patient_login.get('mustChangePassword')} "
      f"patient_id_match={patient_login.get('patientId') == PATIENT_ID}")

# Provider login: still must_change_password=True (we didn't run set-password for them)
# Login should still work with the temp password directly, and return must_change_password=True
prov_login = req("POST", "/auth/login",
    {"email": PROVIDER_EMAIL, "password": TEMP_PWD},
    expect=(200,))
PROVIDER_TOKEN = prov_login.get("accessToken") if isinstance(prov_login, dict) else None
print(f"  provider role={prov_login.get('role')} must_change_password={prov_login.get('mustChangePassword')} "
      f"provider_id_match={prov_login.get('providerId') == PROVIDER_ID}")

# ---------- PHASE 6: GET ME (Authorization header required) ----------
section("GET /auth/me")
# No token -> 401/403
req("GET", "/auth/me", expect=(401, 403))
# Bad token -> 401
req("GET", "/auth/me",
    headers={**AUTH, "Authorization": "Bearer not.a.real.jwt"},
    expect=(401,))
# Patient token -> 200
me_pat = req("GET", "/auth/me",
    headers={**AUTH, "Authorization": f"Bearer {PATIENT_TOKEN}"},
    expect=(200,))
print(f"  /me email={me_pat.get('email')} role={me_pat.get('role')} patient_id={me_pat.get('patientId')}")
# Provider token -> 200
me_prov = req("GET", "/auth/me",
    headers={**AUTH, "Authorization": f"Bearer {PROVIDER_TOKEN}"},
    expect=(200,))
print(f"  /me email={me_prov.get('email')} role={me_prov.get('role')} provider_id={me_prov.get('providerId')}")

# ---------- PHASE 7: LOGOUT (no endpoint; document and assert absence) ----------
section("LOGOUT (no server endpoint - JWT is stateless)")
# /auth/logout shouldn't exist -> 404
req("POST", "/auth/logout", {}, expect=(404, 405))
# After "logout", the token is still mathematically valid until expiry.
# /auth/me with the still-held token continues to work; that's by design.
me_after = req("GET", "/auth/me",
    headers={**AUTH, "Authorization": f"Bearer {PATIENT_TOKEN}"},
    expect=(200,))
print("  -> token remains valid until expiry; logout = client discards token")

# ---------- PHASE 8: DELETE flow cleans up auth ----------
section("DELETE PATIENT/PROVIDER -> auth row removed via patient.deleted / provider.deleted")
req("DELETE", f"/patients/{PATIENT_ID}", headers=CLIN, expect=(204,))
req("DELETE", f"/providers/{PROVIDER_ID}", headers=CLIN, expect=(204,))
time.sleep(1)
final = sql_auth("SELECT count(*) FROM auth_user;")
print(f"[check] auth_user rows after delete cascade: {final} (expected 0)")
PASS += int(final == "0"); FAIL += int(final != "0")

# ---------- SUMMARY ----------
print("\n" + "=" * 60)
print(f"TOTAL: {PASS} passed, {FAIL} failed")
print("=" * 60)
