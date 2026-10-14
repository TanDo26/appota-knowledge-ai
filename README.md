# Internal Knowledge Assistant — MVP (Mission 2, test B)

An assistant that answers questions about internal policies **for a specific person**: it knows who is asking (unit, role, contract type, seniority), only uses documents that person may see *and* that apply to them, picks the governing version when documents disagree, cites its sources, and refuses when it has no grounded answer.

**Live demo:** https://appota-knowledge-ai-hquejyxhvszhcy8ahwbgex.streamlit.app/
(Streamlit Community Cloud may need ~30 s to wake the app up.)

> **All organisations, people, documents and figures are simulated.** No real company names or data are used.

---

## What this MVP sets out to prove

**Hypothesis:** answering *correctly for the right person* is an applicability problem, and it can be solved with code and rules that run **before** the LLM.

Plain RAG finds documents that are *relevant*. It does not know which one *applies* to the asker: the subsidiary's policy or the group's, the probation section or the general one, this year's version or next year's, the policy or the outdated FAQ. That is the riskiest assumption from Mission 1, so it is the part built and tested here. SSO, Drive/Confluence connectors and better semantic search are known integration work and were deliberately left out.

**Evidence, in one screen** (tab *So sánh 2 persona*): the same question "Quy định nghỉ phép của tôi như thế nào?" gives Linh (full-time, Company A, 6 years) Company A's leave policy and gives Minh (intern, Company B) the intern handbook; neither sees the other's sources. A persona without permission never sees restricted content — checked with canary tokens over 80 persona × question runs per mode.

## How it works

```
Persona ─► [1] Context ─► [2] Hard filter ─► [3] Retrieval ─► [4] Resolver ─► [5] Answer + post-check
           (code)          (code)             (BM25)           (rules)         (Gemini, or verbatim text)
                                                                                   │
                                            trace of every step (UI "Trace") ◄─────┘
```

| Step | What happens |
|---|---|
| 1. Context | The persona selector stands in for SSO: unit path, role, contract type, seniority. |
| 2. Hard filter | Permission (ACL by unit subtree and role) → scope (own unit and every unit above, never siblings or children) → audience (`applies_to` at document **and section** level) → status → validity window → `supersedes`. Runs before retrieval, so hidden documents are never scored. |
| 3. Retrieval | BM25 over the surviving sections only. Vietnamese is diacritic-folded (`đ` handled), indexed as syllables + syllable bigrams, with a small synonym table. Abstention uses **question coverage** (share of the question's IDF-weighted terms found in the top section), not the raw score. |
| 4. Resolver | Per topic key: R1 version → R2 audience (a section targeted at your contract type replaces the general one) → R3 document type (`policy > procedure > guideline > faq = announcement`; disagreeing lower sources are flagged to their owner) → R4 org level (`override`, `floor`, `supplement`) → R5 same-level documents with different figures = **CONFLICT**, no silent choice. |
| 5. Answer | Gemini rewrites clear answers as JSON with citations; a post-check rejects any unknown citation or any figure not found in the cited sources or the asker's profile, and falls back to the verbatim text. Conflicts, refusals and personal-data questions never go to the LLM. |

Output states: `ANSWERED`, `ANSWERED_WITH_NOTE` (upcoming version, or a FAQ that disagrees), `CONFLICT`, `ABSTAIN` (one identical message for "no data" and "no permission", plus a contact routed from the question's wording only), `OUT_OF_SCOPE` (personal records such as remaining leave days).

Defences against prompt injection: instruction-like lines are stripped from documents at load time and shown to the owner; sources are wrapped as data in `<source>` tags with `<`/`>` escaped.

## Results

| | Verbatim mode | Gemini mode (`gemini-3.5-flash-lite`) |
|---|---|---|
| Test runs passing (12 cases, 14 persona runs) | 14/14 | 14/14 |
| Leaks (80 persona × question runs) | 0 | 0 |
| Correct refusals / wrong refusals | 3/3 · 0 | 3/3 · 0 |

The headline number hides the interesting part, which is in [docs/TEST_REPORT.md](docs/TEST_REPORT.md): the first run passed every automated check while answering TC02 from the wrong section, and an out-of-suite paraphrase is still answered **confidently on a coincidental word match**.

## Mandatory questions

### 1. Which part did you choose to prove, and why?

The **applicability engine that runs before the LLM**: hard filtering by permission and scope, then rule-based resolution of versions, audiences, document types, organisational levels and conflicts. It is the riskiest hypothesis of Mission 1 — retrieval quality and integrations are known problems with known solutions; deciding *which* rule governs *this* person is not. The MVP shows it works: every case about permissions, versions, audiences and conflicts passes in both modes (TC01, TC03–TC06, TC08, TC09), with 0 leaks, and the LLM is optional — the verbatim mode gives the same decisions.

### 2. What changed from Mission 1, and why?

Full log with dates and reasons: [docs/DECISIONS.md](docs/DECISIONS.md). The main changes:

| Mission 1 | Mission 2 | Why |
|---|---|---|
| Postgres + pgvector + BGE-M3 embeddings | In-memory BM25 | No database on Streamlit Community Cloud; a ~2 GB model is close to the free tier's limits and slow to start; the corpus is small. Cost: weak on paraphrases (TC10 and the out-of-suite probe show exactly this). |
| Metadata per document | Topic key + audience per **section** | Precedence rules only apply when two passages are known to govern the same thing; one group handbook covers many topics and audiences. |
| Rule order: version → level → type | Added an **audience** rule | Probation and intern staff need their own section inside the same document (TC09). |
| LLM-only answers | Added a verbatim mode | Tests the core without an LLM; the demo survives quota exhaustion. |
| ~40 shallow test questions | 12 deep cases + leak matrix | The brief asks for a lesson per case. |
| Raw retrieval score threshold | Question-coverage threshold, fixed once (0.59) on a **separate** calibration set | Raw BM25 scores are not comparable across personas whose visible corpora differ. |
| Main topic = top hit's topic | Main topic = highest summed score across relevant top hits | Found by reading run 1: TC02 answered "how many leave days" with the unpaid-leave section. |
| Gemini 2.5 Flash | Ordered model list, skipping retired/overloaded models | `gemini-2.5-flash` returned 404 "no longer available to new users" during the build. |

### 3. Where does it still fail?

From actual runs, not predictions:

1. **Lexical retrieval matches for the wrong reasons.** "Tuần này tôi không lên công ty vài ngày được không?" ("can I not come to the office for a few days this week?" — written as a remote-work question, though it could also mean taking leave) is answered confidently, in both modes, from the *leave request procedure* with coverage 0.69: the folded word "lên" matches "trở lên". It neither mentions the remote-work policy nor flags the ambiguity. TC10 passes only because "làm ở nhà" is in the synonym table. Wrong refusals happen too: "Hồ sơ hoàn ứng cần những giấy tờ gì?" is refused because the answering section never says "giấy tờ".
2. **Automated checks can pass while the answer is wrong.** Run 1 passed 14/14, yet TC02 answered from the wrong section; expectations were written at document level. Only reading the answers caught it.
3. **The number post-check blocks valid arithmetic.** Gemini's "15 days" for Linh (14 + 1 for 5 years' seniority) is rejected and the verbatim rule is shown instead. Kept strict on purpose: allowing sums/differences would also let "13 days" through — the figure of the archived version.
4. **"Applies to me" is not "I may look it up".** The engineering manager is refused the Platform team's on-call allowance although the manager is allowed to read that document (TC11). Whether that is right is a business decision the data does not settle.
5. **Metadata is trusted.** A wrong `scope_unit`, `applies_to` or `effective_from` produces a confident wrong answer. Mitigations: the metadata linter (Data tab), the "Đang trả lời cho: …" line on every answer, and the trace.

## Run locally

Requires Python 3.11+.

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # optional: add GEMINI_API_KEY
streamlit run app.py

pytest                                         # 83 unit tests
python -m eval.run_eval --mode extractive      # no key needed → eval/results/extractive.md
python -m eval.run_eval --mode gemini          # needs GEMINI_API_KEY → eval/results/gemini.md
python -m eval.calibrate                       # abstain-threshold calibration → eval/results/calibration.md
```

Without a key the app runs in verbatim mode; the Gemini toggle is disabled.

## Deploy (Streamlit Community Cloud)

New app → this repository, branch `main`, main file `app.py`, Python 3.12. In *Secrets* paste:

```toml
GEMINI_API_KEY = "..."
GEMINI_MODEL = "gemini-3.5-flash-lite, gemini-3.1-flash-lite, gemini-3.8-flash"
```

Quota protection on the public app: answers are cached per (persona, question, date, mode), each session is capped at 20 Gemini questions, and quota or model errors fall back to the verbatim text with a banner. Keys live only in Secrets / the git-ignored `secrets.toml`.

## Repository layout

```
app.py                Streamlit UI (Vietnamese): Q&A, two-persona comparison, test runner, data catalogue
core/                 loader · lint · access · text · retrieval · resolver · pipeline · answer · llm · numbers · models
data/                 org.yaml · users.yaml · contacts.yaml · docs/*.md (19 documents with front-matter)
eval/                 cases.yaml (expectations) · calibration.yaml · run_eval.py · calibrate.py · results/
tests/                pytest unit tests
docs/                 implement_plan.md · DECISIONS.md · TEST_REPORT.md · VIDEO_SCRIPT.md
```

## Known limitations

Single-turn only; one topic per question (broad questions get one aspect); lexical retrieval; no real SSO or connectors; no personal records (remaining leave is redirected to HR); conflict detection compares figures only; the injection filter is a regex list; the free Gemini tier is shared and may be slow or exhausted.
