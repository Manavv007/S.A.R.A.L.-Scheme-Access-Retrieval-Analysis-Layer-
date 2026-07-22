# Designing for Data Quality, Not Just Retrieval: What I Learned Building S.A.R.A.L.

*A writeup on the data-quality and evaluation decisions behind S.A.R.A.L. (Scheme Access, Retrieval, Analysis Layer) — a RAG system that helps Indian citizens find government welfare schemes they qualify for.*

[Repo: github.com/Manavv007/S.A.R.A.L.-Scheme-Access-Retrieval-Analysis-Layer-]

---

## The problem, reframed

There are thousands of Indian government welfare schemes, published as dense official PDFs across state and central portals, in inconsistent formats, in six-plus languages. The first version of S.A.R.A.L. I built treated this as a retrieval problem: chunk the PDFs, embed them, run similarity search. It mostly worked — and was also confidently wrong often enough to be dangerous. A citizen being told they're eligible for a scheme they aren't, or missing one they are, isn't a UX bug, it's the whole point of the product failing.

That's when it became clear this was a data-quality problem wearing a retrieval-problem costume.

The failure that made this concrete was about income. My retrieval query was literally `f"Government schemes for a {occupation} in {state} with income {income}"`, so a user earning ₹50,000 got recommended schemes meant for high earners, and a user earning ₹8,00,000 got low-income welfare schemes — the eligibility logic inverted. I spent a while assuming this was a prompt problem: I tightened the eligibility rules, dropped the temperature, added negative constraints. None of it worked, because the retriever wasn't fetching the right documents in the first place. The root cause was that a dense embedding model (`all-MiniLM-L6-v2`) encodes `"income 150000"` and `"income 250000"` as *semantically adjacent* text — it has no representation of the inequality `150000 < 250000`. The exact digits were just noise polluting the semantic space. The fix wasn't a better prompt; it was to strip the number out of the vector query entirely and move the numeric comparison somewhere that can actually do arithmetic. That reframing — "the model can't do the thing I'm asking the vector index to do" — is what turned this from a retrieval-tuning exercise into a data-quality one.

## Decision 1: a canonical schema before anything else

Before touching retrieval quality, I defined one schema — `scheme_id`, `level` (Central/State), `state`, `ministry`, `target_occupation[]`, `caste_eligibility[]`, `income_limit`, `age_min`/`age_max`, `documents_required[]`, `source_url`, `content_hash` — and made the scraper, ingestion pipeline, and retrieval layer all speak it as the single source of truth.

What broke *before* this was the kind of thing that doesn't show up as an error, just as slowly degrading quality:

- **Sub-schemes fragmenting into fake "schemes."** A single program like MSME support was published with named sub-components ("Technology Upgradation," "Rent Reimbursement"), and each got embedded as if it were its own scheme. The user saw the same program three times as three cards. I ended up de-duplicating parsed sub-components back to their parent scheme by name prefix (commit `6aa0c5b`) — but that's a patch on a problem the schema should have prevented.
- **Non-idempotent ingestion.** Early ingestion generated vector IDs non-deterministically, so re-running the pipeline silently *duplicated* everything in the index instead of updating it. Moving to deterministic IDs (`sha1(scheme_id::chunk_index)`) plus a `content_hash` check made re-ingestion a safe, incremental operation.
- **Eligibility fields trapped in prose.** The income limit, age bounds, and state were only present as free text inside the chunk, not as structured, filterable fields. That's *exactly* why the income bug was unfixable at the retrieval layer — there was nothing to filter or compare against, only text to embed.

The lesson I'd generalize: for a system whose entire value is "tell me correctly whether I qualify," the schema you enforce upstream determines what kinds of errors are even possible downstream. Once `state` and `level` were first-class metadata, "don't show a Maharashtra resident a Gujarat-only scheme" became a database filter instead of a hopeful prompt instruction. Retrieval tuning can't fix a bad schema.

## Decision 2: the Researcher-Critic loop — retrieval as an evaluation problem

The retrieval layer runs three strategies (semantic, keyword, national) against Pinecone with server-side metadata filtering, merges results — and then a **Critic LLM judges whether the retrieved context is actually relevant to the user's occupation and state**. On failure, it proposes a refined query and the Researcher retries, up to three times, before candidates go to re-ranking.

This is the part I'd point to as closest to an evaluation-design problem rather than an engineering one. The hard part wasn't wiring the retry loop — it was defining, operationally, what "relevant" means for the Critic to judge against.

The design decision I'm most convinced of is that I scoped the Critic to judge **topic relevance only, explicitly *not* eligibility**. Its prompt asks one thing: are these documents about the right *kind* of scheme for a `{occupation}` in `{state}`? — and it returns strict JSON, `{"verdict": "PASS"|"FAIL", "refined_query": "..."}`. Whether the user actually *qualifies* (income caps, caste, age) is deliberately left to a later, separate step. Collapsing "is this the right topic" and "does this person qualify" into one judgment was the first thing I tried, and it made the Critic's verdicts uninterpretable — a FAIL could mean "wrong documents" or "right documents, ineligible user," and those need opposite responses (refine the query vs. keep the docs and mark ineligible).

The honest part is what happened once the upstream got good. After server-side metadata filtering and an occupation-synonym expansion step (commit `e9b9d84` — mapping "Farmer" → "agriculture krishi," etc.) were in place, the Critic started PASSing on essentially every real query I threw at it. In my logs I almost never saw a FAIL-and-refine actually change the outcome. That told me two uncomfortable things: (a) retrieval had gotten good enough that the Critic rarely earned its latency, and (b) I had no way to distinguish a *correct* PASS from the Critic simply rubber-stamping, because I never validated its judgments against any ground truth. When I later profiled latency, that unvalidated-PASS pattern is precisely what let me add a rule that *skips the Critic entirely* when retrieval already returns a healthy candidate pool — a call I could only justify by observing it wasn't changing outcomes, not by having measured that skipping was safe.

On telling "the Critic is wrong" apart from "the Researcher's retrieval is wrong": the only signal I ever had was manual. When the Critic FAILed and its refined query was nearly identical to the original, that was usually the Critic being over-eager on good documents (Researcher fine, Critic wrong). When retrieval genuinely pulled, say, agricultural *training* schemes for a *student* query — because both texts mention "training" — the Critic's FAIL was correct and the refined keywords fixed it (Researcher wrong, Critic right). I separated these by reading logs, one case at a time. That's not evaluation; it's anecdote, and it's the gap I call out at the end.

## Decision 3: grounding as a hallucination-prevention constraint, not a UI feature

Every verdict the system produces is grounded to the specific scheme's `source_url` and `apply_url` — the model is structurally prevented from asserting a scheme exists without a citable source underneath it.

I did build, and reject, an ungrounded version first. The initial approach just asked the model to "include an official link if you know one." It produced confident, plausible output — scheme names that *sounded* real, sometimes with links that weren't, and occasionally schemes that don't exist phrased exactly like ones that do. For a product whose job is to tell people what benefits they can claim, a fabricated-but-believable scheme is worse than saying nothing.

So I moved grounding out of the prompt and into a post-generation matching step in code. The LLM proposes verdicts; then a matcher walks each returned `scheme_name` back to the metadata of the documents that were actually retrieved (exact match → substring → an overlap threshold of two-plus significant tokens) and attaches the real `source_url` / `apply_url` from the schema. The document checklist comes from metadata too, not the model. The point of enforcing this at the data layer rather than the prompt: a verdict that *can't* be matched to a retrieved source surfaces as **ungrounded**, visibly, instead of arriving as a confident claim with an invented citation.

That choice has a cost I've actually seen. In recent runs the logs reported "0 grounded with a source" on outputs that were otherwise sensible — the model had renamed schemes (abbreviated or partially translated them) enough that my name-matcher missed, so real recommendations came through without their links. That's a matching-*recall* problem, and I'd rather have that failure mode (a correct recommendation with a missing link) than the one I designed it away from (a wrong recommendation with a confident link).

## What I'd measure next

If I kept building this, the next investment wouldn't be a new feature — it'd be a **labeled evaluation set** for the Critic's relevance judgments themselves. Right now the Critic's "relevant / not relevant" call is unvalidated against any ground truth; I'm trusting the LLM's judgment about its own retrieval without an independent check — and, as above, that untrusted trust is what I quietly leaned on when I made the Critic skippable for latency. I'd want:

- A small hand-labeled set of (query, retrieved-doc, correct relevance label) triples, built from real eligibility edge cases — e.g. someone eligible in one state but not a neighboring one, or eligible by occupation but excluded by income threshold — since those are exactly the cases the Critic is most likely to get wrong.
- A way to measure whether the Critic's retries are actually improving relevance, or just adding latency for the same result. (I strongly suspect the latter in most cases, but "suspect" is the problem.)
- Human-reviewed accuracy on the re-ranking step specifically, since that's the step that decides what makes it into the LLM's limited context window.
- A grounding-recall metric: of the verdicts the system was *right* about, what fraction actually got their `source_url` attached? The "0 grounded" episode says that number is sometimes zero, and I currently only find out by reading logs.

## Honest limitations

The system has no human-labeled eval set today — every quality claim I can make is from manual testing, not measured accuracy. The Critic's own relevance judgment is itself unvalidated, which is the failure mode I'd fix first if I extended this. Beyond that, the gaps I actually know about:

- **Grounding recall is brittle.** The name-match between an LLM verdict and its source metadata breaks when the model renames or translates a scheme — the "0 grounded" case. Multilingual output makes this worse, because scheme names get partially localized and drift away from the English metadata.
- **Numeric extraction is unverified.** `income_limit`, `age_min`, and `age_max` are parsed out of dense PDF prose. I deliberately keep numbers out of the vector search and hand the comparison to the LLM at reasoning time — but I have no labeled check that the *extracted* thresholds are correct, so a mis-parsed cap produces a confidently wrong verdict with no alarm.
- **Multilingual eligibility-language ambiguity.** The `reason` field is translated into six languages by the same LLM. I have no check that a translated eligibility statement preserves the exact numeric or legal meaning of the original — "income must not exceed ₹2,50,000" is not a sentence I want paraphrased loosely.
- **PDF parsing edge cases.** Tables and multi-column layouts chunk poorly, and state tagging depends on ingestion conventions that older vectors sometimes lack. Those untagged vectors get dropped by the server-side `state`/`level` filter — a silent false-negative, where a real scheme simply never surfaces because its metadata wasn't clean.

---

*I'm sharing this because the parts of this project I'm least sure about — the Critic that always says yes, the grounding that sometimes grounds nothing — are more interesting to me than the parts that worked cleanly. The clean parts were engineering. The uncertain ones are where the actual problem lives.*
