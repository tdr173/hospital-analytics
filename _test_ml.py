"""Smoke test for ml-batch endpoints with empty DB.

Goal: every endpoint returns a sensible response (not 500). For list/stat
endpoints we expect 200 with an empty payload. For lookup-by-id endpoints
on missing rows we accept 200 (empty), 400, 404, or 422.
"""
import json
import urllib.request
import urllib.error

BASE = "http://localhost"
H = {"Host": "ml.localhost", "Content-Type": "application/json"}
PASS = 0; FAIL = 0


def req(path, expect=(200,), describe=False):
    global PASS, FAIL
    r = urllib.request.Request(BASE + path, headers=H, method="GET")
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            code, raw = resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        code, raw = e.code, (e.read().decode() if e.fp else "")
    except Exception as e:
        code, raw = 0, str(e)
    ok = code in expect
    PASS += int(ok); FAIL += int(not ok)
    mark = "PASS" if ok else "FAIL"
    short = raw[:160].replace("\n", " ")
    extra = f"\n        body: {short}" if (not ok or describe) else ""
    print(f"[{mark}] GET {path:55s} -> {code} (expected {expect}){extra}")


def section(t):
    print(f"\n{'=' * 6} {t} {'=' * 6}")


section("HEALTH")
req("/health")

section("CLUSTERS - list / stats (empty DB OK)")
req("/clusters", describe=True)
req("/clusters/statistics", describe=True)
req("/clusters/categorical-features-statistics", describe=True)
req("/clusters/numerical-features-statistics", describe=True)

section("CLUSTERS - by id (no data, accept any non-500)")
# integer route param; nonexistent cluster
req("/clusters/detail/1", expect=(200, 400, 404, 422))
req("/clusters/ai-analysis/1", expect=(200, 400, 404, 422))
# malformed (string where int expected) -> 422
req("/clusters/detail/abc", expect=(422,))

section("SEQUENCES - list / resources")
req("/sequences", describe=True)
req("/sequences/resources", describe=True)
# pagination/filter knobs should still 200 on empty
req("/sequences?page=1&rows=10&minLength=2&sortBy=support_count&sortType=desc")
req("/sequences?search=foo")

section("SEQUENCES - by id (no data, accept any non-500)")
req("/sequences/ai-analysis/1", expect=(200, 400, 404, 422))
req("/sequences/ai-analysis/abc", expect=(422,))

print("\n" + "=" * 60)
print(f"TOTAL: {PASS} passed, {FAIL} failed")
print("=" * 60)
