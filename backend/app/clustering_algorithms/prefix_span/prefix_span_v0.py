# Prefix Span Initial Implementation

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # backend/app/

from typing import Iterable

import pandas as pd
from dotenv import load_dotenv
from prefixspan import PrefixSpan
from sqlalchemy import text

from db import engine


MIN_SUPPORT_PCT = 0.01 # how many patients have the sequence (22.284 x 0.01)
MIN_PATTERN_LENGTH = 3
MAX_PATTERN_LENGTH = 6
TOP_K = 500            #


def load_events(engine) -> pd.DataFrame:
    query = text("""
        SELECT patient_id, start_date AS event_date,
               'C:'  || TRIM(description) AS item
        FROM condition
        WHERE description IS NOT NULL AND start_date IS NOT NULL
        UNION ALL
        SELECT patient_id, start_date,
               'M:'  || TRIM(description)
        FROM medication
        WHERE description IS NOT NULL AND start_date IS NOT NULL
        UNION ALL
        SELECT patient_id, start_date,
               'P:'  || TRIM(description)
        FROM "procedure"
        WHERE description IS NOT NULL AND start_date IS NOT NULL
        UNION ALL
        SELECT patient_id, start_date,
               'CP:' || TRIM(description)
        FROM careplan
        WHERE description IS NOT NULL AND start_date IS NOT NULL
    """)
    df = pd.read_sql(query, con=engine)
    df["event_date"] = pd.to_datetime(df["event_date"])
    return df

# 70197 careplans
# 727499 conditions
# 913100 medications
# 3225114 procedures
# load events returns all of them -> 4.935.910 events

# print(load_events(engine))

def build_sequences(engine) -> list[list[str]]:
    events = load_events(engine)
    events = events.sort_values(["patient_id", "event_date"], kind="mergesort")
    grouped = events.groupby("patient_id", sort=False)["item"].apply(list)
    return grouped.tolist()

# build_sequences returns a dict of lists, where each list is the patient chronological history.

# print(build_sequences(engine))

def encode(sequences: list[list[str]]) -> tuple[list[list[int]], list[str]]:
    vocab: dict[str, int] = {}
    inv: list[str] = []
    encoded: list[list[int]] = []
    for seq in sequences:
        out = []
        for it in seq:
            idx = vocab.get(it)
            if idx is None:
                idx = len(inv)
                vocab[it] = idx
                inv.append(it)
            out.append(idx)
        encoded.append(out)
    return encoded, inv

# encodes each string to an integer as the prefixSpan lib. works with
# integers, not strings. there are 1172 unique items -> 311 unique C,
# 398 unique M, 423 unique P, 40 unique CP

def pattern_to_str(pattern: Iterable[str]) -> str:
    return " -> ".join(pattern)

def mine(sequences: list[list[str]]) -> list[tuple[int, list[str]]]:
    n_patients = len(sequences)
    abs_minsup = max(2, int(n_patients * MIN_SUPPORT_PCT))

    int_seqs, inv_vocab = encode(sequences)

    ps = PrefixSpan(int_seqs)
    ps.minlen = MIN_PATTERN_LENGTH
    ps.maxlen = MAX_PATTERN_LENGTH

    raw = ps.topk(TOP_K)
    raw = [(sup, pat) for sup, pat in raw if sup >= abs_minsup]

    return [(sup, [inv_vocab[v] for v in pat]) for sup, pat in raw]


def main() -> None:
    load_dotenv()
    sequences = build_sequences(engine)
    n_patients = len(sequences)
    print(f"{n_patients} patient sequences")

    mined = mine(sequences)
    print(f"{len(mined)} patterns\n")

    lines: list[str] = [f"Top {len(mined)} patterns (ranked by support)\n"]
    for rank, (sup, pat) in enumerate(mined, start=1):
        pct = 100.0 * sup / n_patients
        line = f"  {rank:3}. [{sup:5} pts, {pct:5.1f}%] {pattern_to_str(pat)}"
        print(line)
        lines.append(line)

    out_path = "v0.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nsaved to {out_path}")


if __name__ == "__main__":
    main()
