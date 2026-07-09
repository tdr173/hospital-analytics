import sys, os, json

BACK = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
EVAL = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(BACK, "app"))
sys.path.insert(0, EVAL)
os.chdir(BACK)

from dotenv import load_dotenv
load_dotenv(os.path.join(BACK, ".env"))

from db.db_connector import SessionLocal, _db_retrieve
from service.lllm_sql_agent_service.agent_service import run_agent
from gold_queries_50 import QUERIES
import openpyxl
from openpyxl.styles import Font, Alignment


def fmt(rows):
    if not rows:
        return "(no rows)"
    if len(rows) == 1 and len(rows[0]) == 1:
        return str(list(rows[0].values())[0])
    return ", ".join(f"{k}={v}" for k, v in rows[0].items())


def main():
    db = SessionLocal()
    records = []
    for i, q in enumerate(QUERIES, 1):
        question = q["question"]
        try:
            expected = fmt(_db_retrieve(db, q["sql"]))
        except Exception as e:
            expected = f"GOLD ERROR: {e}"
        db.rollback()
        try:
            out = run_agent(db, question, role="MANAGER")
            result = out.get("response", "") if isinstance(out, dict) else str(out)
        except Exception as e:
            result = f"AGENT ERROR: {e}"
        db.rollback()
        print(f"[{i}/50] {question}\n   GOLD : {expected}\n   AGENT: {str(result)[:200]}")
        records.append({"n": i, "question": question, "sql": q["sql"],
                        "expected_result": expected, "result": result})
    db.close()

    json.dump(records, open(os.path.join(EVAL, "eval_results_50.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "SQL Agent 50"
    ws.append(["#", "question", "result", "expected_result"])
    for c in ws[1]:
        c.font = Font(bold=True)
    for r in records:
        ws.append([r["n"], r["question"], r["result"], r["expected_result"]])
    for row in ws.iter_rows():
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 55
    ws.column_dimensions["C"].width = 60
    ws.column_dimensions["D"].width = 45
    wb.save(os.path.join(EVAL, "sql_agent_evaluation_50.xlsx"))
    print("SAVED eval_results_50.json + sql_agent_evaluation_50.xlsx")


if __name__ == "__main__":
    main()
