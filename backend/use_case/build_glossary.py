from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from copy import deepcopy
import re

FOLDER = r"C:\Users\rczxc\Documents\Licenta\hospital-analytics\backend\use_case"
GLOSSARY_PATH = FOLDER + r"\Glossary_updated.docx"
USECASE_PATH  = FOLDER + r"\Hospitai_UseCaseSpecification_updated.docx"
VISION_PATH   = FOLDER + r"\Hospitati_Vision_updated.docx"
GLOSSARY_FILE = "Glossary.docx"   # hyperlink target keeps the final name
HL_REL_TYPE   = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"

# ── 20 glossary terms ────────────────────────────────────────────────────────
TERMS = [
    {
        "term": "Actor",
        "bookmark": "term_actor",
        "searches": ["Primary Actor", "Actor"],
        "definition": (
            "In the context of use cases, an entity (person or external system) that "
            "interacts with the HospitAI platform to achieve a goal. Primary actors "
            "(Doctor, Hospital Manager) initiate use cases; offstage actors (Patient, "
            "University Supervisor) have an interest in the outcome without directly "
            "triggering the flow."
        ),
    },
    {
        "term": "Closed Sequential Pattern",
        "bookmark": "term_closed_seq",
        "searches": ["closed sequential patterns", "closed sequential pattern"],
        "definition": (
            "A frequent sequential pattern for which no super-pattern has the same "
            "support value. Used to eliminate redundancy in PrefixSpan results by "
            "retaining only the most specific patterns from patient event sequences."
        ),
    },
    {
        "term": "Cluster",
        "bookmark": "term_cluster",
        "searches": ["Cluster"],
        "definition": (
            "A group of patients identified by the K-Prototypes algorithm as sharing "
            "similar clinical and demographic characteristics. Each cluster is persisted "
            "in the database together with its narrative summary, representative colour, "
            "and patient count."
        ),
    },
    {
        "term": "Cluster Prototype",
        "bookmark": "term_cluster_prototype",
        "searches": ["cluster prototype"],
        "definition": (
            "The representative data point of a cluster, expressing the dominant feature "
            "values (both numerical centroids and categorical modes) for the group. "
            "Displayed in the HospitAI dashboard to characterise each cluster at a glance."
        ),
    },
    {
        "term": "ETL Pipeline",
        "bookmark": "term_etl",
        "searches": ["ETL Pipeline", "ETL pipeline", "ETL"],
        "definition": (
            "Extract, Transform, Load — the standalone ingestion process that reads "
            "Synthea CSV files, normalises them into the relational PostgreSQL schema, "
            "and materialises derived columns such as patient age and encounter counts. "
            "Runs once per dataset refresh, independently of the FastAPI application."
        ),
    },
    {
        "term": "FastAPI",
        "bookmark": "term_fastapi",
        "searches": ["FastAPI"],
        "definition": (
            "The Python web framework that exposes the analytical API consumed by the "
            "Next.js frontend. Hosts the patient, cluster, statistics, and sequence "
            "routers and enforces JWT-based authentication and role-based access control "
            "on every endpoint."
        ),
    },
    {
        "term": "Feature Distribution",
        "bookmark": "term_feature_dist",
        "searches": ["feature distributions", "feature distribution"],
        "definition": (
            "The statistical distribution of a specific patient feature (e.g. age, "
            "gender, BMI bucket) within a cluster. Displayed in the HospitAI dashboard "
            "through per-cluster bar and pie charts to characterise cluster composition."
        ),
    },
    {
        "term": "Gemini API",
        "bookmark": "term_gemini",
        "searches": ["Gemini API", "Gemini LLM", "Gemini"],
        "definition": (
            "Google's large language model API used by HospitAI to generate "
            "natural-language summaries for each patient cluster and to power the "
            "SQL Agent. Returns plain-language interpretations targeted at "
            "non-technical hospital managers within 5 seconds."
        ),
    },
    {
        "term": "HospitAI",
        "bookmark": "term_hospitai",
        "searches": ["HospitAI"],
        "definition": (
            "The hospital data analytics platform developed as part of this bachelor's "
            "thesis. Provides K-Prototypes patient clustering, PrefixSpan sequential "
            "pattern mining, aggregate statistics dashboards, and an LLM-powered SQL "
            "Agent, all accessible through a React web interface."
        ),
    },
    {
        "term": "JWT",
        "bookmark": "term_jwt",
        "searches": ["JWT"],
        "definition": (
            "JSON Web Token — a compact, URL-safe token format used for stateless "
            "authentication between the React frontend and the FastAPI backend. Each "
            "token encodes the user's identity and role, and is validated on every "
            "API request to enforce role-based access control."
        ),
    },
    {
        "term": "K-Prototypes",
        "bookmark": "term_k_prototypes",
        "searches": ["K-Prototypes"],
        "definition": (
            "The clustering algorithm used to group patients. Extends K-Means by adding "
            "a Hamming-based categorical distance term so that numerical and categorical "
            "features can be clustered jointly without artificial binary encodings. "
            "Provided by the kmodes Python library."
        ),
    },
    {
        "term": "LLM",
        "bookmark": "term_llm",
        "searches": ["LLM"],
        "definition": (
            "Large Language Model — an AI model trained on large text corpora and capable "
            "of generating coherent natural language. Used in HospitAI via the Gemini API "
            "for cluster summarisation and via the SQL Agent for natural-language "
            "database querying."
        ),
    },
    {
        "term": "Material UI",
        "bookmark": "term_material_ui",
        "searches": ["Material UI"],
        "definition": (
            "A React component library implementing Google's Material Design system. "
            "Used throughout the HospitAI frontend to provide consistent, responsive "
            "UI components including tables, buttons, inputs, date pickers, and charts."
        ),
    },
    {
        "term": "PCA",
        "bookmark": "term_pca",
        "searches": ["PCA scatter", "PCA"],
        "definition": (
            "Principal Component Analysis — a dimensionality reduction technique used "
            "to project high-dimensional patient feature vectors into two dimensions "
            "for cluster scatter-plot visualisation in the HospitAI analytics dashboard."
        ),
    },
    {
        "term": "PostgreSQL",
        "bookmark": "term_postgresql",
        "searches": ["PostgreSQL"],
        "definition": (
            "The relational database management system used to persist all ingested "
            "clinical data, clustering results, sequence mining patterns, and user "
            "accounts. Accessed from Python through SQLAlchemy and SQLModel."
        ),
    },
    {
        "term": "PrefixSpan",
        "bookmark": "term_prefixspan",
        "searches": ["PrefixSpan"],
        "definition": (
            "The sequential pattern mining algorithm used to discover frequent ordered "
            "sequences of clinical events across the patient population. Results are "
            "filtered by a minimum support threshold and displayed in descending support "
            "order in the HospitAI Frequent Sequences view."
        ),
    },
    {
        "term": "RBAC",
        "bookmark": "term_rbac",
        "searches": ["RBAC", "role-based access control"],
        "definition": (
            "Role-Based Access Control — an access control model in which permissions "
            "are assigned according to user roles. HospitAI defines four roles — Admin, "
            "Doctor, Patient, and Hospital Manager — enforced at the FastAPI endpoint "
            "level via JWT tokens."
        ),
    },
    {
        "term": "Silhouette Score",
        "bookmark": "term_silhouette",
        "searches": ["Silhouette score", "Silhouette Score"],
        "definition": (
            "A cluster quality metric measuring how similar each patient is to their own "
            "cluster compared to the nearest neighbouring cluster. Ranges from -1 "
            "(misclassified) to +1 (well-separated). Used alongside Davies-Bouldin and "
            "Calinski-Harabasz indices to evaluate K-Prototypes clustering quality."
        ),
    },
    {
        "term": "Support Value",
        "bookmark": "term_support",
        "searches": ["support values", "support value", "descending support"],
        "definition": (
            "A metric in sequential pattern mining indicating the proportion of patient "
            "sequences that contain a given pattern. Patterns are filtered by a minimum "
            "support threshold and displayed in descending support order in the "
            "HospitAI Frequent Sequences view."
        ),
    },
    {
        "term": "Synthea",
        "bookmark": "term_synthea",
        "searches": ["Synthea"],
        "definition": (
            "An open-source patient population simulator used as the source of synthetic "
            "but clinically realistic data for this work. Produces patient demographics, "
            "encounters, conditions, medications, procedures, and observations as CSV "
            "files which are loaded into PostgreSQL via the ETL pipeline."
        ),
    },
]

# ── helpers ───────────────────────────────────────────────────────────────────

def _set_t(el, text):
    t = el.find(qn("w:t"))
    if t is None:
        t = OxmlElement("w:t")
        el.append(t)
    t.text = text
    if text and (text[0] == " " or text[-1] == " "):
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return t


def _add_bookmark(para, name, bid):
    bm_s = OxmlElement("w:bookmarkStart")
    bm_s.set(qn("w:id"), str(bid))
    bm_s.set(qn("w:name"), name)
    bm_e = OxmlElement("w:bookmarkEnd")
    bm_e.set(qn("w:id"), str(bid))
    pPr = para._p.find(qn("w:pPr"))
    idx = (list(para._p).index(pPr) + 1) if pPr is not None else 0
    para._p.insert(idx, bm_s)
    para._p.append(bm_e)


def _make_hl(part, url, text):
    rid = part.relate_to(url, HL_REL_TYPE, is_external=True)
    hl = OxmlElement("w:hyperlink")
    hl.set(qn("r:id"), rid)
    hl.set(qn("w:history"), "1")
    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    rs = OxmlElement("w:rStyle")
    rs.set(qn("w:val"), "Hyperlink")
    rPr.append(rs)
    r.append(rPr)
    _set_t(r, text)
    hl.append(r)
    return hl


def _replace_first(para, search, url):
    """Replace first occurrence of *search* in para's direct runs with a hyperlink."""
    runs_info = []
    pos = 0
    for child in para._p:
        if child.tag == qn("w:r"):
            t_el = child.find(qn("w:t"))
            text = (t_el.text or "") if t_el is not None else ""
            runs_info.append({"el": child, "s": pos, "e": pos + len(text), "t": text})
            pos += len(text)

    if not runs_info:
        return False

    full = "".join(r["t"] for r in runs_info)
    m = re.search(re.escape(search), full, re.IGNORECASE)
    if not m:
        return False

    cs, ce = m.start(), m.end()
    actual = full[cs:ce]

    overlap = [r for r in runs_info if r["s"] < ce and r["e"] > cs]
    if not overlap:
        return False

    first_r, last_r = overlap[0], overlap[-1]
    before = first_r["t"][: cs - first_r["s"]]
    after  = last_r["t"][ce - last_r["s"] :]

    all_ch = list(para._p)
    ins = all_ch.index(first_r["el"])

    # shorten first run to before-text
    _set_t(first_r["el"], before)

    # remove consumed middle/last runs
    for r in overlap[1:]:
        para._p.remove(r["el"])

    # insert hyperlink
    hl = _make_hl(para.part, url, actual)
    para._p.insert(ins + 1, hl)

    # insert after-text run
    if after:
        if last_r is first_r:
            after_run = deepcopy(first_r["el"])
        else:
            after_run = last_r["el"]
        _set_t(after_run, after)
        para._p.insert(ins + 2, after_run)

    return True


# ── Step 1: build Glossary.docx ──────────────────────────────────────────────

def build_glossary():
    doc = Document()
    doc.add_heading("Hospital Analytics – Requirements Glossary", 0)

    for i, t in enumerate(sorted(TERMS, key=lambda x: x["term"])):
        h = doc.add_heading(t["term"], 2)
        _add_bookmark(h, t["bookmark"], i)
        doc.add_paragraph(t["definition"])

    doc.save(GLOSSARY_PATH)
    print(f"Glossary saved → {GLOSSARY_PATH}  ({len(TERMS)} terms)")


# ── Step 2: add hyperlinks to a docx ─────────────────────────────────────────

def process_doc(doc_path):
    doc = Document(doc_path)
    done = set()

    for para in doc.paragraphs:
        if not para.text.strip():
            continue
        for t in TERMS:
            if t["term"] in done:
                continue
            url = f"{GLOSSARY_FILE}#{t['bookmark']}"
            for s in t["searches"]:
                if _replace_first(para, s, url):
                    done.add(t["term"])
                    print(f"  ✓ '{s}'  →  {t['bookmark']}")
                    break

    doc.save(doc_path)
    print(f"  Saved ({len(done)}/{len(TERMS)} terms linked): {doc_path}\n")


# ── main ──────────────────────────────────────────────────────────────────────

print("=== Building Glossary ===")
build_glossary()

VISION_SRC  = FOLDER + r"\Hospitati_Vision.docx"
USECASE_SRC = FOLDER + r"\Hospitai_UseCaseSpecification.docx"

# Copy originals to _updated paths, then process
import shutil
shutil.copy2(VISION_SRC,  VISION_PATH)
shutil.copy2(USECASE_SRC, USECASE_PATH)

print("\n=== Processing Vision_updated.docx ===")
process_doc(VISION_PATH)

print("\n=== Processing UseCaseSpecification_updated.docx ===")
process_doc(USECASE_PATH)

print("Done.")
