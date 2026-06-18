# Pornește backend-ul FastAPI cu PYTHONPATH setat corect.
# Atât backend/ (pentru `from app ...`) cât și backend/app/ (pentru `from db ...`,
# `import domain`, `from repository`) trebuie să fie pe PYTHONPATH.
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$env:PYTHONPATH = "$root;$root\app"
& "$root\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload @args
