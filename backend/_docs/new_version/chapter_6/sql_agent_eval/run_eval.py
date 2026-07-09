import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "app"))
sys.path.insert(0, os.path.dirname(__file__))

from db.db_connector import SessionLocal, _db_retrieve
from service.lllm_sql_agent_service.agent_service import run_agent
from gold_queries import QUERIES

import openpyxl
from openpyxl.styles import Font, Alignment


def format_expected(rows):
    if not rows:
        return "(no rows)"
    if len(rows) == 1 and len(rows[0]) == 1:
        value = list(rows[0].values())[0]
        return str(value)
    if len(rows) == 1:
        parts = [f"{k}={v}" for k, v in rows[0].items()]
        return ", ".join(parts)
    lines = []
    for row in rows[:10]:
        parts = [f"{k}={v}" for k, v in row.items()]
        lines.append(", ".join(parts))
    return " | ".join(lines)


def main():
    db = SessionLocal()
    records = []

    for i, q in enumerate(QUERIES, 1):
        question = q["question"]
        print(f"[{i}/50] {question}")

        try:
            gold_rows = _db_retrieve(db, q["sql"])
            expected = format_expected(gold_rows)
        except Exception as e:
            expected = f"GOLD SQL ERROR: {e}"

        try:
            agent_out = run_agent(db, question, role="MANAGER")
            result = agent_out.get("response", "")
        except Exception as e:
            result = f"AGENT ERROR: {e}"

        records.append({"question": question, "result": result, "expected_result": expected})
        db.rollback()

    db.close()

    with open(os.path.join(os.path.dirname(__file__), "eval_results.json"), "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "SQL Agent Evaluation"

    headers = ["question", "result", "expected_result"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for rec in records:
        ws.append([rec["question"], rec["result"], rec["expected_result"]])

    for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")

    ws.column_dimensions["A"].width = 55
    ws.column_dimensions["B"].width = 60
    ws.column_dimensions["C"].width = 45

    out_path = os.path.join(os.path.dirname(__file__), "sql_agent_evaluation.xlsx")
    wb.save(out_path)
    print("Saved:", out_path)


if __name__ == "__main__":
    main()
