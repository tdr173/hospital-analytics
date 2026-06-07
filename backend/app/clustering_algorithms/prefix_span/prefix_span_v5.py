"""
PrefixSpan v5 - v4 + downstream orchestration.

This is the production version. To avoid duplicating ~450 lines, v5 re-exports
everything from prefix_span.py - they are the same algorithm.

Adds on top of v4:
  - attribute_patients(): resolves which patients each pattern matches
    (inverted index + rarity-ordered intersection + subsequence check)
  - per-cluster mining mode via --n-clusters N (mines clusters 0..N-1 plus -1)
  - DB persistence via save_prefix_span_results (prefix_span_pattern,
    prefix_span_patient_pattern tables)
  - per-run file output (patterns_global.txt / patterns_cluster_<n>.txt)

Run from backend/:
    python app/clustering_algorithms/prefix_span/prefix_span.py [--n-clusters N]
"""

from prefix_span import *  # noqa: F401,F403
from prefix_span import run, _run_single  # noqa: F401
