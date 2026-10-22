# Internal Knowledge Assistant (test B) — Mission 3: improvement

An assistant that answers questions about internal policies **for a specific person**: it knows who is asking (unit, role, contract type, seniority), only uses documents that person may see *and* that apply to them, picks the governing version when documents disagree, cites its sources, and refuses when it has no grounded answer.

**Live demo:** https://appota-knowledge-ai-hquejyxhvszhcy8ahwbgex.streamlit.app/
(Streamlit Community Cloud may need ~30 s to wake the app up.)

> **All organisations, people, documents and figures are simulated.** No real company names or data are used.

---

## Mission 3 — what changed and why

Full report (Vietnamese): **[MISSION3.md](MISSION3.md)** — Before → problem → decision → after → evidence → remaining limits, the test suite, and the three mandatory answers. Decision log: [docs/DECISIONS.md](docs/DECISIONS.md#mission-3--cải-tiến-20102026). Change Request: none assigned yet (20/10/2026).

**Diagnosis first.** Before changing anything, questions written for the five new requirements were run against the Mission 2 code. Every question that is not *"what applies to me, today"* broke: a question about 2025 was refused (the year counted as an unknown word); setting the lookup date to mid-2025 returned the **wrong figure** (the group floor, 12 days, instead of Company A's 2025 policy, 13 days — archived versions were dropped even inside their validity window); a manager asking about a sub-team, or HR asking about probation staff, were refused.

**The main change: three things that Mission 2 merged into "the asker" are now separate.**

| | decides | taken from |
|---|---|---|
| **who asks** | permission (ACL) | the asker's profile — never changes |
| **about whom** | unit scope, contract type | the question if it names one, else the asker |
| **about when** | which version is in force | the question if it names a year/date, else the lookup date |

Permission always stays with the asker, so a lookup for someone else can only narrow what is seen, never widen it. Answers about another subject or time start with a code-inserted line ("… không áp dụng cho bạn", "Theo các tài liệu có hiệu lực ngày …") that survives the LLM rewrite. This also settles Mission 2's open business question (TC11): *may view ⇒ may look up, clearly labelled*.

Smaller changes: a new `CLARIFY` state when the top match is only scattered syllables (Mission 2's real failure "không lên công ty" → "trở lên"); a child unit below a parent `floor` becomes `CONFLICT` instead of silently winning; every citation carries its verbatim text and a content fingerprint, plus the version history and the sources considered but not used.

**Deliberately not done:** semantic retrieval (fixes false refusals but is outside the five requirements, forces re-calibration and is the most regression-prone change); cross-company lookups (the asker would get the group floor presented as the other company's rule); relative dates ("năm sau" is usually the topic, not the time); non-numeric contradiction detection.

**Evidence** — same data, same checker, only the code differs (`python -m eval.compare`, Mission 2 `core/` taken from git):

| Suite | Mission 2 code | Mission 3 code |
|---|---|---|
| Mission 3 suite, 25 runs ([cases_m3.yaml](eval/cases_m3.yaml)) | 11/25 (behaviour\* 15/25) | **25/25** (25/25) |
| Mission 2 suite, 14 runs — regression | 13/13 + 1 changed by design | **13/13** + 1 changed by design |
| Leaks (canary + restricted doc IDs in any public field) | 0 / 174 | **0 / 174** |

\* behaviour = status, sources, answer/note content and flags, ignoring information Mission 2 never produced. Per requirement (behaviour): versions & time 1/5 → 5/5, access by context 6/9 → 9/9, cross-level conflicts 1/2 → 2/2, insufficient evidence 5/7 → 7/7, verification 2/2 → 2/2 (verification adds capability, not a behaviour fix). 12 of the 14 Mission 2 answers are byte-identical; the abstain-threshold calibration is unchanged (17/18) and the new rule flips 0/18 decisions. Expectations were written and run on the old code before `core/` was touched ([run 0](eval/results/m3/run0_before_core_changes.md)). Details: [before_after.md](eval/results/m3/before_after.md).

**Still failing, from real runs:** the `CLARIFY` rule changed exactly one case in the suite (thin evidence); a coincidental *phrase* match still passes ("Khi nào tôi được ký hợp đồng chính thức?" → probation-leave section); the wrong section can still win inside one document ("khung lương khối kỹ thuật" → salary-review section); time/subject understanding is rule-based (no "năm sau", no informal unit names); metadata is trusted; identity is a persona dropdown — SSO is a prerequisite for real users, not an option.

### Mandatory questions (Mission 3)

1. **What did you prioritise, and what did you deliberately not do?** Separating *who asks* from *about whom* and *about when*, because the diagnosis showed it was the common root of the worst failures (versions & time, access by context). Then: ask instead of answering on thin evidence, conflict on floor breaches, verbatim sources. Not done: semantic search, cross-company lookups, relative dates, non-numeric conflicts — reasons above and in [MISSION3.md §2.3](MISSION3.md#23-quyết-định-thay-đổi-gì-không-thay-đổi-gì).
2. **Which change made the biggest difference, and what is the evidence?** The query context. Behaviour on the time and access requirements went from 1/5 and 6/9 to 5/5 and 9/9 on the same suite, data and checker, with no regression on the Mission 2 suite and 0 leaks including a document planted to attack the new lookup. Caveat: the suite is self-written; the stronger evidence is each specific Mission 2 failure with its cause, plus the unchanged regression and calibration results.
3. **Biggest remaining risk if real users get it tomorrow, and what first?** Prerequisite: real identity (SSO + HR master data) — today anyone can pick the HR persona. After that: confident wrong answers where the code cannot tell (coincidental phrase matches, wrong section, wrong metadata), at a rate the self-written suite cannot measure. First: a measured pilot with one company (feedback button, logged traces), the metadata linter as a publishing gate, then semantic retrieval behind the existing access filter, calibrated on the logged real questions.

---

## How it works

```
Asker ─► [1] Query context ─► [2] Hard filter ─► [3] Retrieval ─► [4] Resolver ─► [5] Answer + post-check
         who / about whom /     (code)             (BM25)           (rules)         (Gemini, or verbatim text)
         about when (code)                                                              │
                                             trace of every step (UI "Trace") ◄─────────┘
```

| Step | What happens |
|---|---|
| 1. Query context | The persona selector stands in for SSO (unit path, role, contract type, seniority) and always decides **permission**. *Mission 3:* a year or date in the question sets the date documents are evaluated at (and is removed from the search query); a unit alias (`org.yaml`) or a contract-type phrase sets **whom the answer is about**. Units of another company are not looked up. |
| 2. Hard filter | Permission (ACL by unit subtree and role, for the asker) → scope (subject's unit and every unit above, never siblings or children) → audience (`applies_to` at document **and section** level, for the subject) → status (`draft` never; `archived` only inside its validity window) → validity window → `supersedes`. Runs before retrieval, so hidden documents are never scored. |
| 3. Retrieval | BM25 over the surviving sections only. Vietnamese is diacritic-folded (`đ` handled), indexed as syllables + syllable bigrams, with a small synonym table. Abstention uses **question coverage** (share of the question's IDF-weighted terms found in the top section). *Mission 3:* a top match on scattered syllables only (no phrase of the question, not all of its words) gives `CLARIFY`. |
| 4. Resolver | Per topic key: R1 version → R2 audience (a section targeted at the subject's contract type replaces the general one) → R3 document type (`policy > procedure > guideline > faq = announcement`; disagreeing lower sources are flagged to their owner) → R4 org level (`override`, `floor`, `supplement`; *Mission 3:* a child below a parent `floor` = **CONFLICT**) → R5 same-level documents with different figures = **CONFLICT**, no silent choice. |
| 5. Answer | Gemini rewrites clear answers as JSON with citations; a post-check rejects any unknown citation or any figure not found in the cited sources, the asker's profile or the date asked about, and falls back to the verbatim text. Conflicts, refusals, clarifications and personal-data questions never go to the LLM. *Mission 3:* each citation carries its verbatim text and a content fingerprint; the answer lists the sources considered but not used and the version history of the cited documents (only versions the asker may see). |

Output states: `ANSWERED`, `ANSWERED_WITH_NOTE` (upcoming or current version when asked about another date, or a FAQ that disagrees), `CONFLICT`, `CLARIFY` (Mission 3: evidence too thin — shows the matched words and nearest sections, asserts nothing), `ABSTAIN` (one identical message for "no data" and "no permission", plus a contact routed from the question's wording only), `OUT_OF_SCOPE` (personal records such as remaining leave days).

Defences against prompt injection: instruction-like lines are stripped from documents at load time and shown to the owner; sources are wrapped as data in `<source>` tags with `<`/`>` escaped.

## Run locally

Requires Python 3.11+.

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # optional: add GEMINI_API_KEY
streamlit run app.py

pytest                                         # 118 unit tests (83 from Mission 2)
python -m eval.run_eval                        # Mission 3 suite, no key needed → eval/results/m3/m3_extractive.md
python -m eval.run_eval --suite m2             # Mission 2 suite = regression → eval/results/m3/m2_extractive.md
python -m eval.run_eval --mode gemini          # needs GEMINI_API_KEY → eval/results/m3/m3_gemini.md
python -m eval.compare                         # same suites on Mission 2 code vs current → eval/results/m3/before_after.md
python -m eval.calibrate                       # abstain-threshold calibration → eval/results/m3/calibration.md
```

Without a key the app runs in verbatim mode; the Gemini toggle is disabled. Mission 2's own result files are kept unchanged in `eval/results/` (`extractive.md`, `gemini.md`, `run1/`, `calibration.md`).

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
core/                 loader · lint · context · access · text · retrieval · resolver · pipeline · answer · llm · numbers · models
data/                 org.yaml (with unit aliases) · users.yaml · contacts.yaml · docs/*.md (21 documents with front-matter)
eval/                 cases.yaml (Mission 2) · cases_m3.yaml · calibration.yaml · run_eval.py · compare.py · calibrate.py · results/
tests/                pytest unit tests (test_context.py, test_m3.py are new in Mission 3)
docs/                 implement_plan.md · DECISIONS.md · TEST_REPORT.md · VIDEO_SCRIPT.md
MISSION3.md           Mission 3 report (Vietnamese)
```

## Known limitations

Identity is a persona dropdown (SSO is a prerequisite for real users); single-turn only; one topic per question (broad questions get one aspect); lexical retrieval (false refusals on different wording, coincidental phrase matches still answered); time and subject are read by rules (absolute years/dates and declared unit aliases only; a year is evaluated on 1 January); no cross-company lookups; no personal records (remaining leave is redirected to HR); conflict detection compares figures only; the injection filter is a regex list; the free Gemini tier is shared and may be slow or exhausted.

---

## Mission 2 (previous submission)

### What the MVP set out to prove

**Hypothesis:** answering *correctly for the right person* is an applicability problem, and it can be solved with code and rules that run **before** the LLM.

Plain RAG finds documents that are *relevant*. It does not know which one *applies* to the asker: the subsidiary's policy or the group's, the probation section or the general one, this year's version or next year's, the policy or the outdated FAQ. That is the riskiest assumption from Mission 1, so it is the part built and tested here. SSO, Drive/Confluence connectors and better semantic search are known integration work and were deliberately left out.

**Evidence, in one screen** (tab *So sánh 2 persona*): the same question "Quy định nghỉ phép của tôi như thế nào?" gives Linh (full-time, Company A, 6 years) Company A's leave policy and gives Minh (intern, Company B) the intern handbook; neither sees the other's sources. A persona without permission never sees restricted content — checked with canary tokens over 80 persona × question runs per mode.

### Results

| | Verbatim mode | Gemini mode (`gemini-3.5-flash-lite`) |
|---|---|---|
| Test runs passing (12 cases, 14 persona runs) | 14/14 | 14/14 |
| Leaks (80 persona × question runs) | 0 | 0 |
| Correct refusals / wrong refusals | 3/3 · 0 | 3/3 · 0 |

The headline number hides the interesting part, which is in [docs/TEST_REPORT.md](docs/TEST_REPORT.md): the first run passed every automated check while answering TC02 from the wrong section, and an out-of-suite paraphrase is still answered **confidently on a coincidental word match**.

### Mandatory questions (Mission 2)

#### 1. Which part did you choose to prove, and why?

The **applicability engine that runs before the LLM**: hard filtering by permission and scope, then rule-based resolution of versions, audiences, document types, organisational levels and conflicts. It is the riskiest hypothesis of Mission 1 — retrieval quality and integrations are known problems with known solutions; deciding *which* rule governs *this* person is not. The MVP shows it works: every case about permissions, versions, audiences and conflicts passes in both modes (TC01, TC03–TC06, TC08, TC09), with 0 leaks, and the LLM is optional — the verbatim mode gives the same decisions.

#### 2. What changed from Mission 1, and why?

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

#### 3. Where does it still fail?

From actual runs, not predictions:

1. **Lexical retrieval matches for the wrong reasons.** "Tuần này tôi không lên công ty vài ngày được không?" ("can I not come to the office for a few days this week?" — written as a remote-work question, though it could also mean taking leave) is answered confidently, in both modes, from the *leave request procedure* with coverage 0.69: the folded word "lên" matches "trở lên". It neither mentions the remote-work policy nor flags the ambiguity. TC10 passes only because "làm ở nhà" is in the synonym table. Wrong refusals happen too: "Hồ sơ hoàn ứng cần những giấy tờ gì?" is refused because the answering section never says "giấy tờ".
2. **Automated checks can pass while the answer is wrong.** Run 1 passed 14/14, yet TC02 answered from the wrong section; expectations were written at document level. Only reading the answers caught it.
3. **The number post-check blocks valid arithmetic.** Gemini's "15 days" for Linh (14 + 1 for 5 years' seniority) is rejected and the verbatim rule is shown instead. Kept strict on purpose: allowing sums/differences would also let "13 days" through — the figure of the archived version.
4. **"Applies to me" is not "I may look it up".** The engineering manager is refused the Platform team's on-call allowance although the manager is allowed to read that document (TC11). Whether that is right is a business decision the data does not settle.
5. **Metadata is trusted.** A wrong `scope_unit`, `applies_to` or `effective_from` produces a confident wrong answer. Mitigations: the metadata linter (Data tab), the "Đang trả lời cho: …" line on every answer, and the trace.
