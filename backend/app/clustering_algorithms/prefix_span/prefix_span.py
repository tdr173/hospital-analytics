"""
Frequent sequence mining on patient medical histories.

Implements PrefixSpan (Pei, Han, Mortazavi-Asl et al., ICDE 2001 —
"PrefixSpan: Mining Sequential Patterns Efficiently by Prefix-Projected
Pattern Growth") directly, following the paper's prefix-projected pattern
growth method with pseudo-projection (section 4.3). Each patient's history
is a sequence of *itemsets*: events that share the same calendar day are
grouped into one itemset, so the miner treats them as concurrent rather
than forcing an artificial order between them.

Items are prefixed by their source table so strings from different tables
don't collide:
    E:<encounter_class>        e.g. E:emergency
    C:<condition_description>  e.g. C:Acute viral pharyngitis (disorder)
    M:<medication_description> e.g. M:Lisinopril 10 MG Oral Tablet
    P:<procedure_description>  e.g. P:Computed tomography of head

Run standalone:
    cd backend/app/clustering_algorithms/prefix_span
    python prefix_span.py
"""

from collections import defaultdict
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text

current_folder = Path(__file__).parent

# --- mining parameters -----------------------------------------------------
MIN_SUPPORT = 200         # ~2.5% of patients — lowered so longer patterns survive
MIN_LEN = 3               # total items across all itemsets
MAX_LEN = 6               # short patterns are far easier to interpret
TOP_K_PATTERNS = 200

ENCOUNTER_WHITELIST = {"emergency", "inpatient", "urgentcare", "snf", "hospice"}

# Case-insensitive substrings. Any item whose description contains ANY of these
# is dropped before mining. Synthea's dental module is extremely regular and
# dominates every pattern, so we blacklist it to surface non-dental trajectories.
# Set to an empty set to disable.
ITEM_BLACKLIST_SUBSTRINGS = {
    # dental module — Synthea's regular bundle that dominates every pattern
    # "dental", "gingiv", "plaque", "oral health",
    # "fluoride", "tooth", "teeth", "caries", "gingivitis",
    # routine minor medications / OTC analgesics
    "acetaminophen", "ibuprofen", "naproxen sodium",
    # administrative / workflow items that attach to almost every encounter
    "medication review due", "medication reconciliation",
    "depression screening", "assessment of health and social care needs",
    "assessment of anxiety", "assessment of substance use",
    "screening for domestic abuse",
    # nursing/administrative assessments — present at every inpatient stay,
    # not specific to any disease; they dilute cardiac/obstetric patterns
    "alcohol use disorders identification",
    "screening for drug abuse",
    "morse fall scale",
    "individualized plan of care",
    "initial patient assessment",
    "physical examination procedure",
    # social / status findings — demographics, not clinical events
    "full-time employment", "part-time employment", "unemployed",
    "received higher education", "received primary education",
    "stress (finding)", "body mass index", "obesity (finding)",
    "social isolation",
}

# ---------------------------------------------------------------------------
# Medication generalization: map exact drug names → pharmacological classes.
# Keys are lowercase substrings; first match wins (most-specific first).
# ---------------------------------------------------------------------------
MEDICATION_CLASS_MAP: list[tuple[str, str]] = [
    # Antiplatelet / anticoagulant (check before "aspirin" catches statins)
    ("clopidogrel",        "Antiplatelet"),
    ("ticagrelor",         "Antiplatelet"),
    ("prasugrel",          "Antiplatelet"),
    ("aspirin",            "Antiplatelet"),
    ("warfarin",           "Anticoagulant"),
    ("rivaroxaban",        "Anticoagulant"),
    ("apixaban",           "Anticoagulant"),
    ("dabigatran",         "Anticoagulant"),
    ("heparin",            "Anticoagulant"),
    # Beta-blockers
    ("metoprolol",         "Beta_Blocker"),
    ("carvedilol",         "Beta_Blocker"),
    ("atenolol",           "Beta_Blocker"),
    ("bisoprolol",         "Beta_Blocker"),
    ("propranolol",        "Beta_Blocker"),
    # Statins
    ("simvastatin",        "Statin"),
    ("atorvastatin",       "Statin"),
    ("rosuvastatin",       "Statin"),
    ("pravastatin",        "Statin"),
    ("lovastatin",         "Statin"),
    # Nitrates
    ("nitroglycerin",      "Nitrate"),
    ("isosorbide",         "Nitrate"),
    # ACE inhibitors
    ("lisinopril",         "ACE_Inhibitor"),
    ("enalapril",          "ACE_Inhibitor"),
    ("ramipril",           "ACE_Inhibitor"),
    ("captopril",          "ACE_Inhibitor"),
    ("benazepril",         "ACE_Inhibitor"),
    # ARBs
    ("losartan",           "ARB"),
    ("valsartan",          "ARB"),
    ("candesartan",        "ARB"),
    # Calcium channel blockers
    ("amlodipine",         "Ca_Channel_Blocker"),
    ("diltiazem",          "Ca_Channel_Blocker"),
    ("verapamil",          "Ca_Channel_Blocker"),
    ("nifedipine",         "Ca_Channel_Blocker"),
    ("felodipine",         "Ca_Channel_Blocker"),
    # Diuretics
    ("hydrochlorothiazide","Diuretic"),
    ("furosemide",         "Diuretic"),
    ("spironolactone",     "Diuretic"),
    ("chlorthalidone",     "Diuretic"),
    ("torsemide",          "Diuretic"),
    # Diabetes
    ("metformin",          "Biguanide"),
    ("insulin",            "Insulin"),
    ("glipizide",          "Sulfonylurea"),
    ("glyburide",          "Sulfonylurea"),
    ("sitagliptin",        "DPP4_Inhibitor"),
    ("empagliflozin",      "SGLT2_Inhibitor"),
    ("dapagliflozin",      "SGLT2_Inhibitor"),
    # Respiratory
    ("albuterol",          "Bronchodilator"),
    ("salbutamol",         "Bronchodilator"),
    ("tiotropium",         "Bronchodilator"),
    ("fluticasone",        "Inhaled_Corticosteroid"),
    ("budesonide",         "Inhaled_Corticosteroid"),
    ("beclomethasone",     "Inhaled_Corticosteroid"),
    # Antibiotics
    ("amoxicillin",        "Antibiotic"),
    ("azithromycin",       "Antibiotic"),
    ("doxycycline",        "Antibiotic"),
    ("ciprofloxacin",      "Antibiotic"),
    ("levofloxacin",       "Antibiotic"),
    ("cephalexin",         "Antibiotic"),
    ("trimethoprim",       "Antibiotic"),
    ("penicillin",         "Antibiotic"),
    ("clindamycin",        "Antibiotic"),
    # Opioids / pain
    ("oxycodone",          "Opioid"),
    ("hydrocodone",        "Opioid"),
    ("morphine",           "Opioid"),
    ("tramadol",           "Opioid"),
    ("fentanyl",           "Opioid"),
    # Psychiatric
    ("sertraline",         "SSRI"),
    ("fluoxetine",         "SSRI"),
    ("escitalopram",       "SSRI"),
    ("citalopram",         "SSRI"),
    ("paroxetine",         "SSRI"),
    ("venlafaxine",        "SNRI"),
    ("duloxetine",         "SNRI"),
    ("quetiapine",         "Antipsychotic"),
    ("olanzapine",         "Antipsychotic"),
    ("risperidone",        "Antipsychotic"),
    ("lorazepam",          "Benzodiazepine"),
    ("diazepam",           "Benzodiazepine"),
    ("alprazolam",         "Benzodiazepine"),
    # Corticosteroids (systemic)
    ("prednisone",         "Corticosteroid"),
    ("dexamethasone",      "Corticosteroid"),
    ("methylprednisolone", "Corticosteroid"),
    # Proton pump inhibitors
    ("omeprazole",         "PPI"),
    ("pantoprazole",       "PPI"),
    ("lansoprazole",       "PPI"),
    ("esomeprazole",       "PPI"),
    # Thyroid
    ("levothyroxine",      "Thyroid_Hormone"),
]


def _generalize_medication(description: str) -> str | None:
    """
    Returns a generalized class label if the description matches a known drug
    class, else None (keep original).
    """
    desc_lower = description.lower()
    for substring, cls in MEDICATION_CLASS_MAP:
        if substring in desc_lower:
            return cls
    return None

# Distinct output filename per configuration so successive runs don't overwrite
# each other. Change this when experimenting.
RESULT_FILENAME = "prefix_span_v3_results_clean.xlsx"

# --- DB persistence ---------------------------------------------------------
SAVE_TO_DB = True    # set False to skip DB persistence entirely
OVERWRITE = True     # True  = truncate existing patterns before inserting
                     # False = append to existing patterns (useful for adding
                     #         results from a second run / different config)

# Drop patterns that contain no clinical content (Condition or Procedure).
# Pure encounter / medication chains are rarely insightful on their own.
REQUIRE_CLINICAL_ITEM = True


def _fetch_events(engine) -> pd.DataFrame:
    enc_whitelist_sql = ", ".join(f"'{e}'" for e in ENCOUNTER_WHITELIST)

    events = pd.read_sql(
        text(
            f"""
            SELECT patient_id, 'E' AS item_type,
                   encounter_class AS description,
                   start_date AS event_date
            FROM encounter
            WHERE encounter_class IN ({enc_whitelist_sql})
              AND start_date IS NOT NULL

            UNION ALL

            SELECT patient_id, 'C' AS item_type,
                   description, start_date AS event_date
            FROM condition
            WHERE description IS NOT NULL AND start_date IS NOT NULL

            UNION ALL

            SELECT patient_id, 'M' AS item_type,
                   description, start_date AS event_date
            FROM medication
            WHERE description IS NOT NULL AND start_date IS NOT NULL

            UNION ALL

            SELECT patient_id, 'P' AS item_type,
                   description, start_date AS event_date
            FROM "procedure"
            WHERE description IS NOT NULL AND start_date IS NOT NULL
            """
        ),
        con=engine,
    )

    events["event_date"] = pd.to_datetime(events["event_date"], errors="coerce")
    events = events.dropna(subset=["event_date"])
    events["event_date"] = events["event_date"].dt.normalize()
    events["item"] = events["item_type"] + ":" + events["description"].astype(str)

    # Generalize medication items to pharmacological classes
    med_mask = events["item_type"] == "M"
    generalized = events.loc[med_mask, "description"].apply(_generalize_medication)
    mapped = generalized.notna()
    events.loc[med_mask & mapped, "item"] = "M:" + generalized[mapped]
    n_generalized = mapped.sum()
    print(
        f"generalized {n_generalized}/{med_mask.sum()} medication events "
        f"to drug classes ({events.loc[med_mask, 'item'].nunique()} distinct med items after)"
    )

    print(
        f"fetched {len(events)} raw events | "
        + " | ".join(
            f"{t}={n}"
            for t, n in events["item_type"].value_counts().sort_index().items()
        )
    )
    return events


def _filter_rare_items(events: pd.DataFrame, min_support: int) -> pd.DataFrame:
    """
    Fix (#2): drop items appearing in fewer than `min_support` distinct patients.
    An item below the support threshold can never be part of a frequent pattern,
    so filtering here shrinks the vocabulary without losing valid patterns — and
    preserves rare-but-clinically-interesting items that a global top-K would
    have discarded.
    """
    patient_counts = events.groupby("item")["patient_id"].nunique()
    kept_items = patient_counts[patient_counts >= min_support].index
    filtered = events[events["item"].isin(kept_items)]
    print(
        f"vocabulary after item min-support filter (>= {min_support} patients): "
        f"{filtered['item'].nunique()} distinct items "
        f"({len(filtered)} events, down from {len(events)})"
    )
    return filtered


def build_patient_sequences(engine):
    """
    Returns (sequences, patient_ids, id_to_item) where each sequence is a list of
    itemsets (sorted tuples of *integer item ids*).

    Fix (#4): events sharing a (patient, event_date) pair become one *itemset*.
    Perf: items are deduplicated per patient (keep only the first occurrence of
    each item across the whole sequence) — for frequent-pattern mining where
    support is "distinct patients containing the pattern", repeated occurrences
    of the same item within one patient don't matter, and dropping them turns
    mean sequence length from ~87 to ~20. Items are also integer-encoded so
    downstream set/dict ops are cheap.
    """
    events = _fetch_events(engine)

    if ITEM_BLACKLIST_SUBSTRINGS:
        before = len(events)
        blacklist_lower = {s.lower() for s in ITEM_BLACKLIST_SUBSTRINGS}
        mask = events["description"].str.lower().apply(
            lambda d: any(s in d for s in blacklist_lower)
        )
        events = events[~mask]
        print(
            f"blacklisted {before - len(events)} events "
            f"matching {sorted(ITEM_BLACKLIST_SUBSTRINGS)}"
        )

    events = _filter_rare_items(events, MIN_SUPPORT)

    # integer-encode items
    unique_items = sorted(events["item"].unique())
    item_to_id = {it: i for i, it in enumerate(unique_items)}
    id_to_item = unique_items  # list indexed by id
    events = events.assign(item_id=events["item"].map(item_to_id))

    # dedup: keep the earliest occurrence of each (patient, item)
    events = events.sort_values(["patient_id", "event_date"])
    events = events.drop_duplicates(subset=["patient_id", "item_id"], keep="first")

    sequences = []
    patient_ids = []
    for pid, group in events.groupby("patient_id", sort=False):
        seq = []
        for _, day_group in group.groupby("event_date", sort=True):
            itemset = tuple(sorted(set(day_group["item_id"])))
            if itemset:
                seq.append(itemset)
        total_items = sum(len(s) for s in seq)
        if total_items >= MIN_LEN:
            sequences.append(seq)
            patient_ids.append(pid)

    lens = [sum(len(s) for s in seq) for seq in sequences]
    print(
        f"built {len(sequences)} patient sequences (itemset form, int-encoded, deduped) | "
        f"items per seq: min={min(lens)} max={max(lens)} "
        f"mean={sum(lens) / len(lens):.1f}"
    )
    return sequences, patient_ids, id_to_item


# ---------------------------------------------------------------------------
# PrefixSpan (itemset-aware) — from scratch, following the paper.
# ---------------------------------------------------------------------------
#
# A "projection" is a pointer (seq_id, i, j) into the original database:
#   seq_id = sequence index
#   i      = itemset index within the sequence at which the prefix last matched
#   j      = item index within that itemset (the pivot)
# Extensions fall into two kinds (paper section 2):
#   s-extension : next itemset after i,  pattern grows by a new singleton itemset
#   i-extension : item later than j in itemset i, pattern grows inside its last
#                 itemset (requires the item to be lex-greater than the pivot
#                 to keep the canonical form unique)
# The initial projection uses i = -1 so every itemset is reachable as an
# s-extension.
# ---------------------------------------------------------------------------


def _build_position_index(sequences):
    """
    For each sequence, build a dict item_id -> (i_idx, j_idx). Because items are
    deduplicated per patient, each item has at most one position per sequence,
    so projection is a single dict lookup per seq — no tail scan, no bisect.
    """
    index = []
    for seq in sequences:
        pos = {}
        for i, iset in enumerate(seq):
            for j, item in enumerate(iset):
                pos[item] = (i, j)
        index.append(pos)
    return index


def prefixspan(sequences, min_support, min_len, max_len, item_types=None, verbose=True):
    """
    Returns list of (support_count, pattern, matching_seq_ids) where pattern is
    a list of tuples of int item-ids. Matches come directly from projection.

    Perf: at each recursion, we first compute globally reachable items from the
    projection, then only project for items whose local support >= min_support.
    This is the core anti-monotone pruning from the paper.
    """
    pos_index = _build_position_index(sequences)
    results = []
    calls = [0]

    def scan(proj):
        s_ext = defaultdict(set)
        i_ext = defaultdict(set)
        for sid, i_idx, j_idx in proj:
            # iterate positions of this sequence once
            for item, (pi, pj) in pos_index[sid].items():
                if pi > i_idx:
                    s_ext[item].add(sid)
                elif i_idx >= 0 and pi == i_idx and pj > j_idx:
                    i_ext[item].add(sid)
        return s_ext, i_ext

    def project_s(proj, item):
        out = []
        for sid, i_idx, _ in proj:
            pos = pos_index[sid].get(item)
            if pos is not None and pos[0] > i_idx:
                out.append((sid, pos[0], pos[1]))
        return out

    def project_i(proj, item):
        out = []
        for sid, i_idx, j_idx in proj:
            if i_idx < 0:
                continue
            pos = pos_index[sid].get(item)
            if pos is not None and pos[0] == i_idx and pos[1] > j_idx:
                out.append((sid, pos[0], pos[1]))
        return out

    def grow(pattern, proj, plen, depth=0):
        calls[0] += 1
        s_ext, i_ext = scan(proj)

        # Category-adjacency rule: in the pattern's canonical flattening
        # (itemsets in order, items within an itemset sorted ascending), no two
        # adjacent items may share a category (E/C/M/P). The "previous" item
        # for any extension is pattern[-1][-1] (the last item of the last
        # itemset in the current pattern). Pruning here instead of
        # post-filtering kills entire same-category subtrees early.
        prev_type = None
        if item_types is not None and pattern:
            prev_type = item_types[pattern[-1][-1]]

        def ok(item):
            return prev_type is None or item_types[item] != prev_type

        s_items = sorted(
            ((it, s) for it, s in s_ext.items() if len(s) >= min_support and ok(it)),
            key=lambda x: -len(x[1]),
        )
        i_items = sorted(
            ((it, s) for it, s in i_ext.items() if len(s) >= min_support and ok(it)),
            key=lambda x: -len(x[1]),
        )

        for idx, (item, seqs) in enumerate(s_items):
            if verbose and depth == 0:
                print(f"  [L0 {idx + 1}/{len(s_items)}] item={item} sup={len(seqs)} calls={calls[0]}")
            sup = len(seqs)
            new_pattern = pattern + [(item,)]
            new_len = plen + 1
            if new_len >= min_len:
                results.append((sup, new_pattern, seqs))
            if new_len < max_len:
                grow(new_pattern, project_s(proj, item), new_len, depth + 1)

        for item, seqs in i_items:
            sup = len(seqs)
            new_pattern = pattern[:-1] + [pattern[-1] + (item,)]
            new_len = plen + 1
            if new_len >= min_len:
                results.append((sup, new_pattern, seqs))
            if new_len < max_len:
                grow(new_pattern, project_i(proj, item), new_len, depth + 1)

    initial = [(sid, -1, -1) for sid in range(len(sequences))]
    grow([], initial, 0)
    if verbose:
        print(f"prefixspan done: {calls[0]} recursive calls, {len(results)} patterns")
    return results


# ---------------------------------------------------------------------------


def _format_pattern(pattern, id_to_item):
    """Render pattern as  '(A, B) -> C -> (D, E)'  so itemsets are visible."""
    parts = []
    for iset in pattern:
        names = [id_to_item[i] for i in iset]
        if len(names) == 1:
            parts.append(names[0])
        else:
            parts.append("(" + ", ".join(names) + ")")
    return " -> ".join(parts)


def _has_clinical_item(pattern, id_to_item):
    """Fix (#3): require at least one Condition or Procedure anywhere in the
    pattern. Encounter-only and medication-only chains rarely carry the
    clinical signal we're looking for."""
    for iset in pattern:
        for item_id in iset:
            name = id_to_item[item_id]
            if name.startswith("C:") or name.startswith("P:"):
                return True
    return False


def run():
    load_dotenv()
    from db import engine as db_engine

    print("=" * 60)
    print("PrefixSpan frequent-sequence mining (v1, from paper)")
    print("=" * 60)

    sequences, patient_ids, id_to_item = build_patient_sequences(db_engine)
    # item_types[id] = "E" | "C" | "M" | "P" (parsed from the string prefix)
    item_types = [name.split(":", 1)[0] for name in id_to_item]
    patterns = prefixspan(
        sequences, MIN_SUPPORT, MIN_LEN, MAX_LEN, item_types=item_types
    )

    if REQUIRE_CLINICAL_ITEM:
        before = len(patterns)
        patterns = [p for p in patterns if _has_clinical_item(p[1], id_to_item)]
        print(f"filtered {before - len(patterns)} patterns with no condition/procedure")

    print(f"mined {len(patterns)} frequent patterns (min_support={MIN_SUPPORT})")

    if not patterns:
        print("no patterns reached min_support; lower MIN_SUPPORT and retry.")
        return

    # --- Stratified top-K: top TOP_K_PER_LENGTH per length bucket, sorted by
    # support descending within each bucket, then assembled longest-first.
    TOP_K_PER_LENGTH = 75
    from collections import defaultdict as _dd
    by_length: dict[int, list] = _dd(list)
    for item in patterns:
        plen = sum(len(iset) for iset in item[1])
        by_length[plen].append(item)

    selected = []
    for length in sorted(by_length.keys(), reverse=True):
        bucket = sorted(by_length[length], key=lambda x: x[0], reverse=True)
        selected.extend(bucket[:TOP_K_PER_LENGTH])

    print(
        "stratified selection: "
        + ", ".join(
            f"len={l}: {min(len(by_length[l]), TOP_K_PER_LENGTH)}"
            for l in sorted(by_length.keys(), reverse=True)
        )
    )

    patterns_df = pd.DataFrame(
        [
            {
                "rank": i + 1,
                "support_count": sup,
                "support_pct": round(100 * sup / len(sequences), 2),
                "length": sum(len(iset) for iset in pat),
                "pattern": _format_pattern(pat, id_to_item),
            }
            for i, (sup, pat, _) in enumerate(selected)
        ]
    )

    print(f"\nTop patterns (stratified by length):")
    with pd.option_context("display.max_rows", None, "display.max_colwidth", None):
        print(patterns_df.to_string(index=False))

    out_xlsx = current_folder / RESULT_FILENAME
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        patterns_df.to_excel(writer, sheet_name="patterns", index=False)
        # one sheet per length bucket for easy browsing
        for length in sorted(by_length.keys(), reverse=True):
            bucket = sorted(by_length[length], key=lambda x: x[0], reverse=True)
            df_bucket = pd.DataFrame(
                [
                    {
                        "rank": i + 1,
                        "support_count": sup,
                        "support_pct": round(100 * sup / len(sequences), 2),
                        "pattern": _format_pattern(pat, id_to_item),
                    }
                    for i, (sup, pat, _) in enumerate(bucket[:TOP_K_PER_LENGTH])
                ]
            )
            df_bucket.to_excel(writer, sheet_name=f"len_{length}", index=False)

    print(f"\nwrote results to {out_xlsx}")

    if SAVE_TO_DB:
        from save_results_sequences import save_sequence_results
        save_sequence_results(
            engine=db_engine,
            patterns=selected,
            patient_ids=patient_ids,
            id_to_item=id_to_item,
            format_pattern=_format_pattern,
            overwrite=OVERWRITE,
        )
        # Report actual patient coverage in the junction table
        covered = set()
        for _, _, seq_ids in selected:
            covered.update(seq_ids)
        print(
            f"persisted {len(selected)} patterns to DB (overwrite={OVERWRITE}) | "
            f"covered {len(covered)}/{len(sequences)} patients "
            f"({100 * len(covered) / len(sequences):.1f}%)"
        )


if __name__ == "__main__":
    run()
