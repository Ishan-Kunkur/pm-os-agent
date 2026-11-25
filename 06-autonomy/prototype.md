# Prototype: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 1, the working agent demo
>
> ✅ **What this validates:** the agent actually runs end to end, by the end you'll have proven it with real screenshots of your Cortex across the six required moments (M2 to M6).

## What it does

Cortex is a PM chief-of-staff prototype that turns a task brief and local project fixtures into a source-grounded status-update draft and proposed backlog stories. It retrieves evidence, checks the draft through an independent critic, and stops for human review. Runtime limits bound iterations, revisions, time, and estimated spending; explicit override attempts are refused by an input guard. It cannot publish updates, change tickets, or make launch commitments. Live connectors and specialist agents remain planned, and recorded grounding and critic failures show why it still needs active human oversight.

## How you built it

- **Coding agent:** Codex, directed through guided module decisions.
- **Model + bounds:** `gpt-4o-mini` for drafting and the separate critic; 8 iterations, 2 revision attempts, 90-second work deadline, $0.10 estimated/run, $0.50 estimated/day, and at most 10 proposed stories. Human approval remains required; local estimated spending controls are not exact provider billing ceilings.
- **Repo / config:** Build in `00-build/agent.py`, `critic.py`, `tools.py`, `prompts.py`, and `daily_budget.py`. Local configuration uses the gitignored `00-build/.env`; example settings are in `00-build/.env.example`.
- **Deployment:** Local fixture-based CLI; no live deployment yet. Live connectors and specialist agents remain planned.

## Screenshots (required, collected M2 to M6)

Real screenshots of *your* Cortex running. These are the `00-build/CORTEX-ANATOMY.md` set and they are required, a link alone is not enough.

| # | Screenshot | Caption | From |
|---|---|---|---|
| 1 | ![Happy-path draft and HITL](evidence/01-happy-hitl.jpg) | Recorded M2 run: validated draft and four proposals held for PM review; no publication. | M2 |
| 2 | ![Critic rejection and revision](evidence/02-critic-rejection.jpg) | Controlled M3 test: real critic rejects injected 75% against 41% source evidence; revision fires, with later false-positive escalation preserved. | M3 |
| 3 | ![Grounded and withheld-source comparison](evidence/03-grounding-probe.jpg) | Recorded M4 probes: refreshed claims grounded in activity; withheld source leads to invented PRs, invalid critic response, and runtime-blocked success followed by escalation. | M4 |
| 4 | ![Guarded jailbreak refusal](evidence/04-jailbreak-refusal.jpg) | M5 input guard flags/refuses this explicit override and escalates before model/task-tool calls. Pattern-specific protection, not universal detection. | M5 |
| 5 | ![Two-iteration bound trip](evidence/05-bound-trip.jpg) | Recorded M5 run: temporary two-iteration cap stops work with evidence held and no success claim. | M5 |
| 6 | ![M6 end-to-end run](evidence/06-end-to-end.jpg) | Fresh 2026-11-21 fixture run: all five critic checks pass; three story proposals held for review; four iterations, zero revisions, estimated $0.0020. | M6 |

**Capture provenance:** These are actual browser screenshots retaken on 2026-11-25 at 1440 pixels wide of a local evidence viewer showing verbatim excerpts from recorded stdout; they are not contemporaneous terminal screenshots or fabricated terminal images. Views 1–5 show previously recorded runs; view 6 shows the fresh capstone run. The HTML viewers and full source traces are retained in `evidence/`. They document observed behavior, including failures, and do not establish the four-week advancement gate.

## How to run it

_Minimal steps for someone to reproduce the demo (env vars, and the command or the coding-agent prompt you used)._

## Evidence summaries

Full transcripts are stored in [evidence/](evidence/); [detailed run notes](evidence/run-notes.md) preserve the test setup, outcomes, source mapping, and limitations.

### M3 critic rejection evidence

A controlled bad draft claimed 75% activation against 41% source evidence. The real critic rejected it and the production revision path fired. Positive controls later accepted the correct value, but false positives and malformed critic responses occurred during development. See [M3 run notes](evidence/run-notes.md#m3-critic-rejection-evidence) and [captured rejection trace](evidence/m3-structured-loop-trace.txt).

### M4 grounding verification

The refreshed run cited 41% → 43%, PRs #820/#823, and issue #825. With activity withheld, Cortex invented PRs and a no-open-issues claim. Its critic response was invalid; the runtime's required-evidence check blocked success and Cortex escalated. This is not proof of reliable semantic hallucination detection. See [grounded trace](evidence/m4-grounded-final-trace.txt), [withheld-source trace](evidence/m4-withheld-final-trace.txt), and [source mapping and limitations](evidence/run-notes.md#m4-grounding-verification).

### M5 bounds and jailbreak proof attempts

Early jailbreak runs missed the injection or escalated for cross-project Sev-1 confusion. These failures remain in the [detailed evidence](evidence/run-notes.md#m5-bounds-and-jailbreak-proof-attempts), rather than being erased by the later successful guard test.

### M5 guarded jailbreak proof

A code-level guard subsequently flagged, refused, and escalated the explicit override fixture before model/task-tool calls, at zero API cost. It catches selected phrases, not every injection. See the [guard trace](evidence/m5-jailbreak-guard-proof.txt).

### M5 iteration-bound trip

A command-scoped two-iteration limit stopped happy-path work without a success claim. Available evidence and locally proposed stories were held; no tickets were created. The normal limit remains eight. See the [bound-trip trace](evidence/m5-iteration-bound-proof.txt).

### M5 reflection

The human sees the refusal or stop reason, available evidence, and a clear handoff. The jailbreak was blocked before model or tool calls, and the iteration test stopped at two steps. No update was published, no tickets or launch gates changed, and no date was committed. I would implement the 90-second overall timeout next so a single hung call cannot bypass the protection provided by the iteration limit.

**Follow-up:** The timeout was subsequently implemented, along with the daily ledger and local stop/resume control. [Detailed notes and offline test results](evidence/run-notes.md#m5-timeout-implementation-follow-up) explain the POSIX/local scope, estimated-spend limitations, and simulated tests. Future deployment needs shared equivalents; CI and broader model reliability gates remain uncompleted.

### M6 end-to-end evidence

The fresh 2026-11-21 fixture run retrieved Northstar's Sprint 25 activity, passed all five critic checks, and held three proposed stories for human review. Four iterations, zero revisions, estimated $0.0020, 21.665 seconds. Nothing published. Proposed stories still need PM review, including whether completed work should be proposed again.

[Full M6 trace](evidence/m6-end-to-end-trace.txt) · [Evidence viewer](evidence/06-end-to-end.html)
