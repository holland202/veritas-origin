# COLD-REVIEW-002 registration: paired seeded-defect benchmark, four models, hint-free, hard $10 cap

Status: **REGISTERED, NOT RUN.** No API call has been made for this experiment. Nothing below is a result.

Written by Claude (Sonnet 5.5), which also wrote the corpus builder, the runner and the scoring rule, at Chad Holland's
direction on 2026-10-13. Chad has not reviewed it line by line. Not independent: a Claude-family model designing and
scoring a test of Claude-family models. Spending is authorized by Chad as direction given on 2026-10-13 (up to about
$10 of his own API credit); the run itself is started by him.

## What is weak, before anything runs

- **Same family.** All four reviewers are Claude models and so is the author of the test. This ranks Claude models
  against each other. It says nothing about other vendors' models or about human review.
- **Contamination.** `sovereign-veritas` is public. A model may have seen the original files. The seeded mutations are
  new (made with a fixed seed on 2026-10-13) but sit inside code that may be familiar. The known defect (base 0, from
  COLD-REVIEW-001) is public and written up, so a HIT there may be recall.
- **Some mutants may be harmless.** A single-token change (`<` to `<=`, `and` to `or`, dropping `not`, flipping a
  returned `True`/`False`) does not always change behavior in a way a reader can detect from the file alone. I did
  not hand-check the 21 mutants for equivalence, because choosing by hand would add my bias. So the ceiling on
  detection is below 100% by an unknown amount, and a low win rate is not by itself proof that a model is bad.
- **Mechanical scoring only measures the planted site.** A model that finds a real, different bug in the file gets no
  credit and no penalty in the pair classification. Findings are saved verbatim; a person should read some.
- **Small n.** 22 bases (1 real, 21 seeded). Exact sign tests are reported, with the understanding that 10 to 20
  discordant pairs give very wide uncertainty.
- **Thinking models and truncation.** `max_tokens` is 8000 including thinking tokens. A reply cut off at the
  limit is recorded as `TRUNCATED`, kept, and never counted as "no finding".
- **Cost bound is an estimate.** Input tokens are estimated at 1 token per 2.5 bytes, deliberately pessimistic. If a
  tokenizer disagrees, the runner records real usage, and the report says so. The Console bill is the true figure.
- **Probably will not spend the full $10.** The cap is a worst-case bound (every reply hitting `max_tokens`). Real
  replies are shorter, so real spend is expected to be well under $10. The runner keeps going in cycles until tasks
  run out or the next one cannot fit under the bound, and then stops.

## The experiment

**Corpus** (`corpus.py`, seed `20261013`, pinned to sovereign-veritas commit `fff4f68f5a775212de344af6afc9d1f099e71457`).
For each eligible kernel file (1,200 to 13,000 bytes, with at least one mutation site inside a function body), the
builder picks one mutation site with a seeded RNG, never by hand, and writes two files: **CLEAN** (the file as it is)
and **DEFECT** (the same file with that one token changed; the line count and every other line are identical). Mutation
operators: comparison flip (`==`/`!=`, `<`/`<=`, `>`/`>=`), `and`/`or` swap, dropped `not`, `return True`/`return False`
flip. Every DEFECT file compiles. Base 0 is the real pair from COLD-REVIEW-001 (defective `execute(action)` vs fixed
`execute(decided_action)`), not a mutation.
Result: 22 bases (1 real, 21 seeded), 44 files. `corpus/manifest.json` sha256 `3126a37e…4a3d2`; rebuilding from the
pinned commit reproduces the corpus byte for byte.

**Models:** `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`, `claude-fable-5-1`. Message Batches API
(50% off). No temperature or other settings. Prompt `prompt.txt`, sha256 `e7576934…9c4b5`: hint-free, says the file may
contain no defect, asks for JSON with `line`, `quoted_code`, `severity`, `explanation`. Each file is shown with line
numbers (`NNNN| code`).

**Requests:** each (model, base, role) once as rep 1 (primary analysis). If budget remains, rep 2 as a top-up
(descriptive only). Up to 352 requests; the cost guard decides how many are sent.

### Scoring (fixed now, mechanical)

A reply is `OK` if it is not truncated and parses as JSON with a `findings` list. Otherwise `TRUNCATED`, `PARSE_FAIL`,
`ERRORED`, `EXPIRED`, `CANCELED` or `NO_RESULT`. None of those is ever "no finding".
A file's **site flag** is true if any finding has `line` equal to the planted line, or its `quoted_code` contains the
planted line's text **and** that text appears on exactly one line of the file. For a DEFECT file the planted line is
the mutated line; for a CLEAN file it is the same location in the unmutated file.
For a (model, base, rep), when both files are `OK`:

| DEFECT flagged | CLEAN flagged | Class |
|---|---|---|
| yes | no | **win** (found the defect, did not flag the good version) |
| no | yes | **reversed** |
| yes | yes | both (cannot discriminate) |
| no | no | neither |

Only win vs reversed is discordant. Per model: exact two-sided sign test on wins vs reversed.

### Registered predictions (primary analysis: rep 1)

| ID | Prediction |
|---|---|
| P1 | On the bases that all four models completed (need at least 8), wins are ordered `fable >= opus >= sonnet >= haiku` (ties allowed) |
| P2 | The model with the most wins finds at least 50% of the seeded defects as wins (need at least 8 seeded common bases) |
| P3 | Control cleanliness: for every model, the CLEAN-site flag rate over seeded bases is at most 10% (need at least 8 OK CLEAN replies per model) |
| P4 | On base 0 (the real SV-ATTACK-001 defect), at least 2 of the 4 models score a win |
| P5 | Pooled over models, `bool_swap` and `drop_not` mutants are won at a higher rate than `compare_flip` mutants (need at least 12 model-base cells in each group) |
| P6 | At least 95% of submitted requests come back `OK` |

I have no strong prior for P1. I expect P5 to be the least safe: boundary flips may be harder to see, but a `Haiku`
that guesses may do the opposite. I do not know whether P2 holds. A failure of any of these is a result and is kept.

**Unrun prediction (the door), P7:** repeat variance. Rep 2 data may allow a descriptive agreement number, but no
prediction about it is registered or evaluated here. Also unrun: a second seed, and a non-Claude reviewer.

## Anti-vacuity

`python3 -I cold_review2.py selftest` must print `SELFTEST PASS` before a run. It does not use the network. It checks:
the scorer (truncation, prose, fenced JSON, line match, unique-quote match, non-unique quote rejected, bad `line`
value); the corpus (every file compiles, hashes match the manifest, mutation pairs differ in exactly the registered
line, base 0 present); the task list and cost guard (refuses over the cap, refuses while a batch is uncollected,
never resubmits); and five fake detectors run end to end through the real submit/collect/analyse code with an
in-process stand-in for the API:

| Fake detector | Required outcome |
|---|---|
| oracle (flags only the planted line in DEFECT) | all wins; sign test significant; P4 passes |
| flag-everything | zero wins, zero reversed (cannot discriminate), and **P3 fails** |
| anti-oracle (flags only CLEAN) | all reversed; P2 fails |
| silent (always `{"findings":[]}`) | all neither; P2 fails |
| garbage (prose) | zero parsed; **P6 fails**; nothing counted as "no finding" |

Self-test result at registration (2026-10-13, container, Python 3): 91 checks `ok`, last line `SELFTEST PASS`.

`mutants.py` mutates the runner itself seven ways and requires the self-test to fail each time:

```
KILLED   scorer flags everything
KILLED   win/reversed swapped
KILLED   truncation treated as OK
KILLED   budget cap removed
KILLED   uncollected-batch gate removed
KILLED   resubmission allowed
KILLED   parse failure counted as clean
MUTANTS ALL KILLED
```

`plan` output at registration (no network):

```
bases 22  tasks 352 (4 models x 2 files x 2 reps)  max_tokens 8000  cap $10.00 worst-case
prompt sha256 e757693445467a1ee7335cebc89d75a463423e0398969b43af3c7cf40879c4b5
  haiku  rep-1 requests  44  worst case $  0.10  per request max $0.0024
  sonnet rep-1 requests  44  worst case $  1.94  per request max $0.0470
  opus   rep-1 requests  44  worst case $  3.87  per request max $0.0940
  fable  rep-1 requests  44  worst case $  9.69  per request max $0.2350
  all rep-1 tasks worst case $15.60 (cap $10.00); the staged guard decides how far it gets from ACTUAL spend
first batch (pilot): 16 requests, worst case $1.45, spent so far $0.0000
guaranteed minimum requests if every request hit max_tokens: 114; at most 352
```

Hashes at registration: `cold_review2.py` `c163ec7a…480d`, `corpus.py` `83c4b617…`, `mutants.py`
`9ff865b4…6a56`. Verify with `sha256sum` before running.

## Run rules

1. **One authorized execution:** `python3 -I cold_review2.py auto --yes-usd 10`, started by Chad on his own device with
   his own key, only after the self-test passes and he writes that he authorizes it. The command refuses to start
   without exactly `--yes-usd 10`.
2. The runner sends the **pilot** first (the first 2 bases, all four models, both files, 16 requests), waits for it,
   and stops without spending more if no pilot reply parsed. A model with no `OK` pilot reply is dropped from the main
   run and reported as a failure.
3. After each batch is collected the runner re-reads actual spend from returned `usage` and only then sizes the next
   batch. The bound is: actual spend of collected batches + worst-case of anything pending + the new batch &le; $10.00,
   and no single batch has a worst case above $4.00.
4. A request is never submitted twice. No retries. Raw result files are never overwritten.
5. The key is read from the environment only; never printed, written, committed or pasted. Delete the key in the
   Console afterwards.
6. If the run is interrupted, `status`/`collect` resume it. That is the same execution, not a new one.
7. Do not add Oleksandr Shuliak's report, or anything derived from it, to any input or prompt. The corpus is public
   code only.
8. Evidence (`results/`) is committed unedited with `SHA256SUMS`. Failed predictions are kept and marked.
9. A second run needs a separate written authorization from Chad.

## What a result would and would not establish

If P1 to P6 mostly pass: on this public codebase and these seeded single-token defects, hint-free review by these four
Claude models ranked as predicted, with a measured false-alarm rate on the unmutated twin. It would still not show
reliability on real unknown bugs, not rule out recall, and not be independent validation. If they fail, the failure
tells us how far a cold single-file review can be trusted before we lean on it.
