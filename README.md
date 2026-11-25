# Nova 4B: measured reliability work on a small model

This repository documents **CORE-4B**, the first stage of **Nova**, a European general-purpose model project run by a solo founder (Hexon). The question was simple: can a compact model (**Qwen3.5-4B + LoRA**) be made reliable on professional tasks where a wrong answer is costly?

Three failure types were studied:
- **Reasoning on case files.** Deciding whether a file is admissible when facts are false, unknown or disputed between sources.
- **Exact calculations and dates.** Amounts, discounts, durations and calendar offsets.
- **Missing inputs.** The model must not silently invent a value that the request does not give.

The work ran from late September to early October 2026, on rented GPUs (RunPod, usually one RTX PRO 4500) and on the founder's own RTX 5070. One person directs AI coding agents, and reviewers are also AI models (see *Limits*). Reports and code comments are in French; this README is the English entry point.

## What is in this repository

| Folder | Content |
|---|---|
| `reports_fr/` | The original campaign reports, in French, numbered in time order. Each one states the pre-registered decision first. |
| `src/tool_use/` | The calculation tool, in the model's native tool-call format: a restricted Python runner, the call parser, the router, the agent loop with its retry guard and fallback, the scoring, and the pre-registered decision script. The protocol is included. |
| `src/blind_review/` | The tools used to build masked review packs and lock them by hash before unblinding, the reviewer guide, and the verdict classifier. |
| `src/gradient_check/` | The check of training gradients against a float32 truth, used to choose the training runtime. |
| `data/toolcalc_sample.jsonl` | 50 real cases from the tool study, with the model's answers with and without the tool. |
| `results/toolcalc_r2_RESULTS.json` | The full measured output of the tool study's decision script. |

## How the work is run

The rules below were applied to every campaign, and the reports show each of them.

- **Decisions are pre-registered.** The protocol, the thresholds and the decision script are frozen by SHA-256 before any result exists. The decision comes from the script, not from a reading of the results. If one criterion fails, the result is "not demonstrated", even when the rest looks good.
- **Benchmarks run on raw inputs.** The production input normaliser is never applied to a benchmark, so it cannot hide a weakness.
- **Reviews are blind.**
  - Answers are anonymised, merged across arms and shuffled.
  - Each reviewer's file is locked by hash before the key is opened.
  - Two reviewers work separately: Claude, and a GPT-based assistant used by the founder ("Astra" in the reports).
  - Disagreements go to a blind arbiter, and agreement (kappa) is reported.
- **New test sets come from someone else, after the freeze.** For the missing-input work, Astra wrote each blind set after the code and the analysis were frozen.
- **A sealed test stays closed.** A general benchmark (GENBENCH2) is kept unopened, because its first use would spend it. It will serve once, for a final decision.
- **Code checks come before paid reviews.** Many critical errors (invented values, broken JSON) can be found by code. Code gates run first, and reviews look at what code cannot judge.
- **Designs are attacked before launch.** Before a GPU run, the second reviewer tries to break the gates and the data design. Each finding is answered in writing and fixed, or rejected with a reason.

## Results

All numbers are measured. "VF" means the right final value in the answer.

### 1. Reasoning on case files (R2 → R2F, then production choice)

**Task.** A case file lists requirements and sourced facts. Some facts are refuted ("le relevé contredit : …"), some are disputed between two sources, and some are simply missing. The model must answer *recevable* (admissible), *irrecevable* (not admissible) or *indéterminé* (cannot be decided), and justify it.

**Weakness found.** The model read "unknown" or "disputed" as "false", and missed refutations written in some forms.

**R2F** (targeted contrast data, 2 seeds, 216 entries from 4 new domains):

| Group (n) | R2F seed 1 | R2F seed 2 | Previous model R2 (seeds 1 / 2) | Threshold |
|---|---|---|---|---|
| Decisive refuted fact (44) | 44 | 44 | 6 / 0 | ≥ 40 |
| Opposed sources (32) | 28 | 30 | 10 / 5 | ≥ 24 |
| False fact next to a disputed one (4) | **0** | **2** | 0 / 0 | **≥ 3** |
| Non-regression (94) | 94 | 94 | 92 / 92 | ≥ R2 − 2 |

- **Pre-registered decision: not demonstrated.** The small conjunction group failed on both seeds.
- **Blind second pass:** 396 answers, with 396/396 agreement with the automatic classifier.

**Production choice (PREPROD R1).** Three systems × 2 seeds were judged blind on 190 new cases, for verdict, fact statuses, coherence and justification together.

| System | Joint score (both seeds) | Incoherent answers |
|---|---|---|
| R2 + normaliser | 290 / 380 | 31 |
| R2F + normaliser | 367 / 380 | 12 |
| R2G + normaliser | 372 / 380 | 8 |

- The pre-registered rule picked R2G, by 5 cases.
- On general tasks, R2G had more confirmed errors: 24 and 17, against 17 and 13 for R2F. Most came from copying text instead of rephrasing it.
- The founder kept **R2F**, the cautious alternative the report offered.

### 2. Did the adaptation damage the base model? (BASECOMP R1)

Same GPU, same 377 entries, blind judges, two passes on general tasks:

| Measure | Production (R2F) | Base Qwen3.5-4B |
|---|---|---|
| Case-file logic, joint score (/128) | **116** | 49 |
| General tasks, failures confirmed by both passes (/249) | **104** | 117 |
| Categories with ≥ 3 more failures (the "introduced weakness" threshold) | none | — |

- The remaining general weaknesses are mostly **inherited** from the base model.
- **Calculations and dates are the first cause of failure for both models.** This led to the tool study (section 4).
- One weakness is **ours**: a false fact next to a disputed one is concluded "cannot be decided".

### 3. Choosing a training runtime by checking gradients

Before a new training run, the gradients of each runtime were compared with a float32 truth: same weights, same rows and same loss.

| Runtime | Relative L2 error, group 0 | Group 1 | Stable |
|---|---|---|---|
| Standard bf16 (transformers + PEFT) | 0.110 | 0.099 | yes |
| Unsloth, compiled trainer | **0.329** | 0.123 | no: depends on history |
| Unsloth, compile off, its own Triton kernels for Gated DeltaNet | 0.059 | **0.187** | yes |
| **Unsloth, compile off, pure-torch Gated DeltaNet (kept)** | 0.126 | 0.075 | yes |

- **Finding:** the compiled path can start a run in a wrong state. Separately, Unsloth's own kernels for the Gated DeltaNet layers give larger gradient errors on this model and GPU (Blackwell, Triton 3.6).
- **Cost:** about $0.26 and $0.30 for the two tests.
- **Limits:** one run per mode, on six rows. It measures gradient accuracy, not training quality.

### 4. An exact-calculation tool (TOOLCALC R1 and R2): retained on dev

**Setup.** The model gets one tool, `executer_python`, in Qwen3.5's native tool-call format. The tool is a restricted Python runner: an allow-list of modules, an AST check and a separate process. The model can make 3 tool rounds at most.

**R1, on 184 calculation, date and transformation cases (142 never seen before):**

| | Without tool | With tool |
|---|---|---|
| Right final value | 59 | **120** |
| Exact answer (character for character) | 41 | 103 |

- **Gains and regressions:** 63 robust gains and 2 regressions; sign test p ≈ 10⁻¹⁶.
- **Simple families** (amount, discount, duration, date offset, percentage): 12/12 each with the tool.
- **Multi-step families stay weak:**
  - cents rules: 14/32;
  - calendar with closures: 9/32;
  - text transformation: 10/32.

  Most of these errors are well-run programs that encode the rule wrongly. The tool removes arithmetic errors, not misunderstanding.
- **R1 damaged other tasks.** The model called the tool in 73 of 148 non-calculation cases, and lost 6 answers, mostly to retries of the same invalid code.

**R2 fixed the integration, not the model:**
- a lexical router offers the tool only for calculation, date or transformation requests;
- a guard stops identical retries;
- a fallback serves the direct answer when the tool path fails.

On **542 fresh non-calculation requests**: 0 leaked tool markup, 0 missing answers and 0 exact-match losses. The calculation gain was unchanged (59 → 120).

**Blind review of the 36 writing answers changed by the router:**
- content: 15 gains and 8 regressions;
- no new critical error;
- 11 critical errors of the production model fixed.

The pre-registered verdict was **INTEGRATION_VALIDEE_DEV**, with router A retained. All 8 regressions happened *without* any tool call: declaring a tool in the prompt changes some writing answers.

**The sample in `data/`:** 50 never-seen cases from the 5 simple families. Their references were recomputed independently by code. The model is right on **26 / 50** without the tool and **50 / 50** with it. The multi-step families, where the tool helps much less, are not in the sample.

**Not done yet:** confirmation on the sealed test.

### 5. Training the model to use the tool (TOOLTRAIN R1 and R2): rejected

**R1, one seed.**
- The calculation gain was large: VF 194 → 237 / 276.
- The blind review found **15 new critical errors**, among them values invented when an input was missing.
- Verdict: to be revised.

**R2, redesigned and 2 seeds, $3.39.** The redesign added missing-input examples, more replay and stricter code gates, and went through several rounds of adversarial review.
- The calculation gain held: net +40 and +38, p < 10⁻⁵.
- The strict gate found 4 to 6 new content errors per seed, for a limit of 0.
- **Verdict: NON_RETENU.**

A general data mix (R3) had been rejected earlier, after a masked review: no positive signal, and critical regressions confirmed by exact calculation.

### 6. Missing inputs: training failed, a code guard works

**The problem.** When an input of a calculation is missing, the model often fills it in silently. Published work (for example When2Call and AbstentionBench) shows this is common across models, and that scale or reasoning does not fix it.

**Training to signal missing data (2 attempts): rejected.**
- Inventions fell from 23 to 7, then to 12.
- But the model lost right answers, refused complete requests and regressed on calculation families.
- The damage did not depend on the dose.
- Conclusion: training on this base was stopped.

**A code guard (final version: guard B v2).**
- It checks whether every input of a **written formula** is given.
- It abstains whenever the text might state a default value.
- It replaces a numeric answer with a "missing data" message only when it is sure.

Guard B was measured once, end to end, on a blind set written by Astra after the freeze:
- inventions on written formulas: **21 → 2** (in both remaining cases the served answer was still the missing-data signal);
- **0 / 97** right values lost.

Version 2 fixes one defect found afterwards. It serves the same answers on all three end-to-end campaigns, and it is in production. Formulas written in words and free text are **not covered**. Earlier versions that tried to understand default rules failed on each new blind set, so that approach was dropped.

### Production chain

R2F seed-1 adapter + input normaliser + guard B v2. Decoding is greedy, with no thinking mode and 768 tokens. The tool integration (router A + fallback) is validated on dev and waits for the sealed test.

## What is not published, and why

The goal is to make the work **understandable and checkable**, not copyable as is. These parts stay private:

- **Training data generators and corpora.** They are our main asset. The reports describe what each corpus contained.
- **LoRA adapter weights.**
- **Input normaliser rules and guard code.** The method and the measurements are described above; the rule sets are not.
- **Test sets with answer keys, and reviewer keys.** Publishing them would spend them as tests.
- **The sealed benchmark (GENBENCH2).** It has never been opened, even by us.
- **Internal tooling:** pod launchers, the budget ledger and the project's memory database.

The 50-case sample, `results/toolcalc_r2_RESULTS.json` and the reports show real outputs and real decisions.

## Limits

- **The data is synthetic and French.** The tasks and test sets were written by the same AI-assisted process, except the blind sets written by Astra. There is no external benchmark here.
- **The sets are small,** often 8 to 48 cases per group, so differences of a few cases are noise. The reports give exact tests where they matter.
- **Reviewers are language models** (Claude and a GPT-based assistant) working blind. Their agreement is reported, but no large human annotation was done.
- **Most results are on development sets.** Generalisation will only be claimed after the sealed test.
- **The code was written by AI coding agents under the founder's direction.** Some scripts expect the original folder layout and will not run as is. `src/tool_use` runs and is tested standalone.

## Running the tests

```bash
cd src/tool_use
python test_tool_use.py
```

The tests need Python 3.11+ and no GPU, network or model. Model replies are scripted, and every program they run is written in the test file.

`sandbox.py` is a restricted runner for model-written arithmetic, not a security boundary proof. On Linux it also sets resource limits. On Windows it relies on the AST check, the import guard and the timeout only.

## Related work

- [nova-verified-code-data](https://github.com/TrueBebert/nova-verified-code-data): test-verified code data and an agent harness for the next stage, which distills GLM-5.3 into Qwen3.5-122B-A10B on EuroHPC.

## License

The code is under Apache-2.0 (see `LICENSE`). The reports and the sample are released under the same terms. Every case in them is fictional.
