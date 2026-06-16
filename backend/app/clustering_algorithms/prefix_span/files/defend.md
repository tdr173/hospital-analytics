# Defending the PrefixSpan pipeline

This document maps every part of the pipeline (v0–v6, 20 improvements) onto:
- what came from the literature (cite it accurately),
- what is your own engineering (own it, defend it on its merits),
- how to structure the thesis chapters around it,
- the high-pressure committee questions and how to answer them.

The honest split is roughly one-third literature, two-thirds your own engineering. Trying to fake citations for the engineering is the fastest way to lose a defense. The engineering parts are *strengths* when defended on empirical grounds - present them that way.

---

## 1. Things to cite (from the literature)

| Improvement | Source |
|---|---|
| **PrefixSpan algorithm** | Pei, Han, Mortazavi-Asl, Pinto, Chen, Dayal, Hsu. *"PrefixSpan: Mining Sequential Patterns Efficiently by Prefix-Projected Pattern Growth"*, ICDE 2001. PDF is in this folder. Cite for v0. |
| **Pseudo-projection** | Same paper, §4.2. Cite when explaining what the `prefixspan` library does internally. |
| **Closed sequential patterns (`closed=True`)** | Yan, Han, Afshar. *"CloSpan: Mining Closed Sequential Patterns in Large Datasets"*, SDM 2003. Or the stronger/newer one: Wang, Han. *"BIDE: Efficient Mining of Frequent Closed Sequences"*, ICDE 2004. Cite for v2. |
| **Lift as interestingness measure** | Brin, Motwani, Ullman, Tsur. *"Dynamic itemset counting and implication rules for market basket data"*, SIGMOD 1997. Or Piatetsky-Shapiro 1991 for the original notion of a "rule-interestingness" measure. Cite for v3. |
| **Survey of interestingness measures (lift family)** | Tan, Kumar, Srivastava. *"Selecting the right objective measure for association analysis"*, Information Systems 29(4), 2004. Cite when justifying *why* a lift-family measure rather than plain support. |
| **Jaccard similarity / near-duplicate detection** | Jaccard 1901 is the original but nobody cites it for set similarity any more - it's textbook. Cite either Manning, Raghavan, Schütze. *Introduction to Information Retrieval*, 2008, Ch. 19, or Broder. *"On the resemblance and containment of documents"*, 1997 (shingling + Jaccard for near-dup detection). |
| **Inverted index (used in `attribute_patients`)** | Manning, Raghavan, Schütze. *Introduction to Information Retrieval*, 2008. Standard IR primitive. |

Rules of thumb for citing:
- Only cite what you actually use. The committee will check.
- Don't cite the 1901 Jaccard paper for what is now textbook math - cite the IR textbook.
- The PrefixSpan PDF is in the folder; assume your committee has it.

---

## 2. Things to own as your own engineering

These are *your* contributions. Don't fake a citation. Defend each on empirical grounds - observed failure modes, sensitivity to tuning, motivated by domain.

| Improvement | How to defend it |
|---|---|
| **Sort tie-break (C → M → P → CP)** | Determinism: identical input must produce identical sequences for reproducibility. The specific order encodes a clinical-flow assumption (diagnosis precedes treatment precedes intervention precedes care-plan). |
| **Item blacklist** | Empirical. List the items, show their per-patient frequency (>99% of sequences), show they carry no clinical signal. The list is small and exhaustive. |
| **730-day window** | Justify on clinical grounds (recent history reflects current patient state). If asked, mention a sensitivity check at 365 / 1095 days. |
| **Per-patient event cap (25)** | Computational. PrefixSpan cost scales with sequence length. Cite typical sequence-length distributions in your dataset. |
| **Consecutive-duplicate collapse** | Standard preprocessing, no citation needed. Removes refill artifacts that inflate support without adding signal. |
| **Overmine ×20 + post-rerank** | Frame as "mine-and-rerank", a standard pattern in IR (Manning textbook). The 20× factor is empirical - defend with: at lower factors the pool was too thin for diversification to operate, at higher factors runtime grew without changing the top-K. |
| **GML formula (geomean lift, log form)** | This is the v3 contribution to defend most carefully. Position it as: *lift, generalized from 2 items to k items via geometric mean, computed in log space for numerical stability*. Cite Tan et al. 2004 for the lift family; explicitly claim the geomean generalization as your design. The reasoning is in §3b of `how.md` (length-comparability, weakest-link semantics, underflow avoidance). |
| **Type-diversity bonus (×(1 + 0.3·(n_types − 1)))** | 100% yours. Domain motivation: clinical *trajectories* cross event types (condition → medication → procedure), and a top-K dominated by within-type co-occurrence misses trajectory-shaped patterns. The 0.3 weight is empirical - present ablations (0.1, 0.3, 0.5) if the committee will probe it. |
| **Run-of-3-same-type filter** | 100% yours. Heuristic. Justify with concrete examples of what it removes (refill chains, Synthea dental protocol blocks). |
| **Explicit closedness post-pass** | Engineering refinement layered on top of the library's CloSpan-style local pruning. Frame as: "library's `closed=True` is correct *within the PrefixSpan recursion tree*, but we rerank globally by GML - a global pass catches residual same-support dominators that the local pruning could not see". |
| **Jaccard threshold (0.80)** | The *choice* of Jaccard you can ground in Broder/Manning. The *threshold* is empirical - failure modes at 0.70 (drops legitimately distinct patterns sharing 3/5 items) and at 0.90 (lets near-duplicates with one substituted item through) are your defense. |
| **Per-prefix cap (6), per-suffix cap (20)** | 100% yours. Defend with the "diabetes flooding" problem: without the cap, ~35 of the top-100 patterns all started with `C:diabetes`. The asymmetric values (6 vs 20) are themselves a defensible choice - prefixes are intent-defining, suffixes are convergent endpoints, so we allow more suffix variety. |
| **Dental cap (15) + DENTAL_KEYWORDS list** | 100% yours, hardcoded to Synthea's behavior. Be upfront: *"this is a dataset-specific safety valve for a known Synthea artifact; reuse on other datasets would require revisiting"*. This honesty is a strength - it shows you understand the limits of your own pipeline rather than presenting it as universal. |
| **Per-cluster mining mode** | Engineering integration with your k-prototypes clustering. No literature claim. Justify as: per-cluster patterns are far more clinically interesting than global ones because each cluster is a phenotype. |
| **`attribute_patients` (inverted-index + rarity-ordered intersection)** | The inverted index itself is from Manning et al. The specific composition (build posting lists once, intersect rarest-first, verify with subsequence check) is engineering. Defend the rarity-first ordering as a standard query-optimization heuristic. |
| **SDOH / social-status drop (v6)** | 100% yours, dataset-specific. Same mechanism as the blacklist but a separate list with its own justification: these are social-determinant "status" findings Synthea attaches to nearly every adult wellness visit, all feeding one screening battery. Defend it as a deliberate domain decision (kept separate from the administrative blacklist *on purpose*), and note the concrete procedure-level battery survives - only the trivial social prefix is dropped. |
| **Multi-type trajectory quota (v6)** | 100% yours. A *guarantee* layered on the v4 top-K selection, not a new filter. Motivation: genuine full-spectrum trajectories (C→M→P→CP) often have low support and get crowded out of top-K by the M+P-heavy pool even with the type-diversity bonus. Defend the two-phase design (reserve up to 25 four-type patterns bypassing the prefix/suffix caps, then capped greedy fill, then re-sort by GML so rank still reflects score). The thresholds (4 types, 25 slots = 5% of TOP_K) are empirical knobs. |
| **Cross-scope dedup (v6)** | Engineering integration with the per-cluster mode. No literature claim. Justify: a high-support chain otherwise appears in the global scope *and* in every cluster, drowning the per-cluster value (a *distinctive* phenotype). Dropping patterns already stored globally forces the per-cluster output to be cluster-distinctive. Be upfront about the ordering dependency: the global scope must be mined first. |

---

## 3. Where each piece lives in the thesis

Three chapters, three roles.

### 3.1 Related Work / Background chapter

One paragraph each on:
- **Sequential pattern mining and PrefixSpan.** Cite Pei et al. 2001. Explain the projection idea in 4–6 sentences. Mention pseudo-projection as the optimization the library implements.
- **Closed sequential patterns.** Cite CloSpan (Yan et al. 2003) or BIDE (Wang & Han 2004). One paragraph contrasting frequent / closed / maximal.
- **Interestingness measures for association rules.** Cite Brin et al. 1997 for lift, Tan et al. 2004 for the survey. Frame as motivation for moving beyond support.
- **Near-duplicate detection.** Cite Manning et al. textbook (Ch. 19) or Broder 1997. Frame as motivation for set-similarity-based dedup in the top-K selection.

Total length: 1.5–2 pages. Don't pad. Don't cite anything you don't use.

### 3.2 Methodology / Design chapter

This is where you commit to the literature-vs-yours split honestly. Recommended structure:

1. **Problem statement.** What we are mining and why. One page.
2. **Algorithm choice.** Why PrefixSpan and not GSP, SPADE, FreeSpan. Two paragraphs.
3. **Library selection.** What the `prefixspan` library implements (classical + pseudo-projection + top-K heap), what it does not (no scoring, no diversity).
4. **Novel design contributions.** Explicit list - preferably a table - separating "from literature (cited above)" from "design contributions of this work". This is *the* honesty-and-clarity move that makes the rest of the thesis credible.
5. **For each design contribution:** definition → motivation → defense (failure modes observed, sensitivity to parameters).

The honesty in section 4 - saying *the dental cap is dataset-specific, the type-diversity bonus weight is empirical, the per-prefix cap is heuristic* - is exactly the kind of self-aware framing committees reward.

### 3.3 Implementation chapter

The v0 → v6 ladder is unusual but powerful: present it as a literal sequence of sections. Each section's content is small:
- What changes from the previous version (one short list).
- What the change costs (lines of code, runtime impact if measurable).
- What the change buys (concrete failure mode it removes, ideally with a before/after pattern from real data).

This is *ablation-as-narrative*. You are not just telling the committee "the pipeline has 20 improvements"; you are showing them, version by version, that you understand why each one is there. That is much stronger than a single-page recipe.

---

## 4. Committee questions and how to answer them

The high-pressure questions you will get and how to handle each.

**Q: "Where does GML come from?"**
A: "Lift is from Brin et al. 1997. The generalization from 2 items to k items via geometric mean is our design decision, motivated by (a) numerical stability - the product of k small probabilities underflows in float64, while log-space geomean does not, and (b) length-comparability - without the k-th root, patterns of different lengths cannot be ranked against each other meaningfully. The choice of geometric mean over arithmetic comes from the weakest-link semantics: a pattern containing one rare item should be considered rare overall."

**Q: "Why Jaccard 0.80 and not 0.75 or 0.85?"**
A: "Empirical. At threshold 0.70 the dedup was aggressive enough to drop legitimately distinct patterns that happened to share 3 of 5 items. At 0.90, near-duplicates with one item substituted - for instance the same diabetic monitoring chain with `P:foot_exam` swapped for `P:hba1c_test` - leaked into the top-K. 0.80 was the threshold where dedup was effective without false positives."

**Q: "Did you invent the type-diversity bonus?"**
A: "Yes. The motivation is that clinical *trajectories* cross event types - a diagnosis leading to a medication leading to a procedure tells a richer story than three medications in a row. We wanted those trajectory-shaped patterns to be ranked higher than within-type co-occurrence. The multiplicative `(1 + 0.3·(n_types − 1))` form is the simplest functional shape that gives a monotone bonus; the 0.3 weight was tuned empirically and we are happy to discuss ablations."

**Q: "Why is the dental cap not a general per-category cap?"**
A: "Two reasons. First, no other category in our dataset exhibited the same flooding behavior - diabetes was controlled by the per-prefix cap, dental was not because it spans procedures, conditions, and care-plans simultaneously. Second, a generic per-category cap would penalize legitimately frequent categories. The dental cap is therefore a targeted, dataset-specific filter; on a non-Synthea dataset this rule would need to be revisited or removed entirely."

**Q: "How is your PrefixSpan implementation different from the original 2001 paper?"**
A: "The algorithm itself is unchanged - we use the `prefixspan` Python library which implements classical PrefixSpan with pseudo-projection (Pei et al. §4.2). The library adds a top-K heap with early termination and supports the CloSpan-style closed-pattern pruning of Yan et al. 2003. Our work layers preprocessing, lift-based scoring, set-similarity diversification, and downstream orchestration on top of that mining call. None of those layers modify the PrefixSpan recursion."

**Q: "What if the cluster has no diabetic patients - does your pipeline still work?"**
A: "Yes. The prefix/suffix caps don't bind unless an item reaches the cap, so absence of diabetes simply means more slots are available for whatever conditions *do* appear. The dental cap likewise binds only when dental-majority patterns reach 15. The minimum-support floor (1% of patients) protects against degenerate top-K on small clusters." *(Verify this before the defense by running on the smallest cluster.)*

**Q: "Why not just use the library's `topk(closed=True)` and stop there?"**
A: "The library returns the K patterns of highest support. On clinical data that top-K is dominated by trivial high-support items and by one-domain flooding - the Synthea dental protocol alone fills 40+ of the top-100 slots. Lift-based reranking surfaces patterns that are statistically *surprising* given baseline frequencies; set-similarity diversification ensures the K slots are spent on distinct findings rather than near-duplicates. The v0-vs-v5 comparison on the real dataset is the empirical justification."

**Q: "If GML already has a type-diversity bonus, why do you also need the multi-type quota?"**
A: "The bonus changes the *score*, but score alone doesn't guarantee *survival* of top-K. A genuine four-type trajectory (condition → medication → procedure → care-plan) usually has low support, so even with the ×1.9 bonus it can sit low in the GML-ranked pool and be crowded out by dozens of medication+procedure co-occurrences with comparable scores, or killed by the per-prefix/suffix caps. The quota reserves up to 25 slots (5% of TOP_K) for full-spectrum patterns, letting them bypass the prefix/suffix caps - they're still Jaccard- and dental-deduplicated, so we don't reintroduce near-duplicates. After both phases we re-sort the whole chosen set by GML, so the quota guarantees inclusion without distorting the final ranking. The thresholds (four types, 25 slots) are empirical."

**Q: "Doesn't bypassing the caps for the quota reintroduce the flooding the caps were meant to prevent?"**
A: "No, because the quota only bypasses the *prefix/suffix* caps, not the Jaccard dedup or the dental cap, and it requires all four event types to be present - that's the strictest diversity condition, so by construction these patterns are the opposite of single-domain flooding. And it's bounded to 25 patterns. The flooding the caps prevent is many near-identical single-lead chains; a four-type trajectory is exactly the rare, broad pattern we *want* to protect."

**Q: "Did you compare PrefixSpan to other sequential pattern miners (SPADE, GSP, FreeSpan)?"**
A: Honest answer. If yes, present results. If no: "We did not. PrefixSpan was selected because its pattern-growth structure and projection-based recursion are well-suited to the long, sparse sequences typical of EHR data; the original paper's experimental evaluation shows it outperforming GSP and FreeSpan on similar workloads. An empirical comparison on our dataset was out of scope for this thesis." (Acceptable if framed honestly.)

**Q: "How do you know your patterns are clinically meaningful?"**
A: This is the hardest question. Honest answers:
- "Pattern interpretability was assessed qualitatively - the top patterns were reviewed by [advisor/clinical reviewer if applicable]."
- "Quantitative validation against external clinical guidelines was out of scope; this thesis focuses on the mining and ranking methodology."
- If you have any clinical sign-off, mention it. If not, *do not pretend you do*.

---

## 5. The single biggest pitfall to avoid

Do not overclaim authorship of the algorithm itself.

- **Wrong:** "We developed an optimized PrefixSpan algorithm."
- **Right:** "We implemented the PrefixSpan algorithm of Pei et al. 2001 using the `prefixspan` Python library, and built a dataset-specific preprocessing, scoring, and diversification pipeline on top."

The committee will ask exactly this question. Get the framing right and the rest of the defense is easier.

---

## 6. The single biggest strength to lean on

You have a *layered ablation* (v0 → v6) where every layer has a defensible reason. That is rare in a thesis. Lean on it:

- "Here is the bare algorithm" (v0).
- "Here is what changes if we add preprocessing X" (v1).
- "Here is what changes if we add scoring Y" (v3).
- … and so on through v6.

The committee gets a clear *causal story* of why every piece is there, with the ability to ask "what would happen at v3 alone?" and get a concrete answer. Most theses cannot do this. Use it.
