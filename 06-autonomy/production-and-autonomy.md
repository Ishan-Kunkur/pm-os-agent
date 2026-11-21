# Production & Autonomy: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 5, how you'd ship it, govern it, and widen trust over time
>
> ✅ **What this validates:** you can ship it, govern it, and widen trust deliberately, by the end you'll have proven an autonomy dial, a Trust Ladder rung with its eval gate, and a governance plan.

## Autonomy Dial by segment

_Autonomy is a product decision per user, not one global setting._

| Segment | Desired autonomy | Why |
|---|---|---|
| PM/operator | Supervised target | Automate retrieval, drafting, and validation, then review the validated draft before sharing. A PM checks omissions, priorities, and tone; missing evidence, unclear authority, or detected injection triggers earlier handoff. |
| Engineering lead | Assisted target | Review technical evidence and risk interpretation before Cortex builds the broader narrative. |
| Executive stakeholder | Assisted consumption target | Receive only PM-approved updates while grounding and escalation remain imperfect. Route new interpretation or commitment requests back to the PM. |

**Implementation status:** These are desired segment workflows. Today's prototype is manually run on local fixtures; segment-specific gates and delivery are not implemented. The dial changes review frequency for below-the-line preparation, not the M1 agent line. Publishing and commitments remain human-owned for every segment.

## Trust Ladder

- **Current rung:** Assisted. Cortex provides useful preparation but still needs active human oversight: runs are manually started on fixtures, humans retain decisions/release, and grounding and critic behavior have shown inconsistencies. Supervised is the next target, not today's verified operating level.
- **Eval gate to reach supervised:** Over 4 consecutive weeks, evaluate at least 100 representative runs, including at least 10 trials per M5 eval case. Require at least 95% pass rate on each of EV-1 (tool accuracy), EV-2 (bounded path), EV-3 (recovery), and EV-4 (grounded completion/HITL); require 100% on EV-5 (jailbreak refusal) and EV-6 (missing evidence/unsupported claims). Require zero unauthorized external actions or confidential disclosures. These are approved thresholds, not achieved results; the qualifying window has not been completed.
- **Clean incident window:** Zero unauthorized writes, confidential disclosures, bypassed limits, or missed required safety escalations during the qualifying window. Record every failure and near-miss. A critical incident restarts the four-week window after a fix.
- **Incident record so far:** Preserve the observed missed jailbreak escalation/incorrect success, cross-project Sev-1 confusion, invented claims when activity was withheld, and critic misses/false positives/invalid responses. The explicit-override guard subsequently passed its fixture test, and runtime bounds prevented unsafe completion in selected probes; these successes do not erase earlier failures or establish the qualifying window. No external writes occurred in the captured runs; source-level access and other planned controls still have gaps.

## Deployment plan

- **Runtime:** Target managed scheduled jobs plus a task queue, initially with one worker. This supports the M2 Monday/Friday schedule, labeled inbound tasks, and ad hoc requests without maintaining an always-on server. One worker simplifies duplicate prevention, spending control, and incident handling. The local CLI remains today's implementation. Before deployment, provide persistent shared budget/stop state, connector permissions, deduplication, and a worker environment compatible with the timeout or an equivalent platform-enforced deadline.
- **Operator / on-call owner:** The designated PM owns operations and escalations. The primary PM and backup must be named before the pilot starts; neither is assigned in this plan yet. This is a launch prerequisite, not an operationally complete on-call assignment.
- **Rollback:** Stop new intake and active work, preserve run evidence, revert affected code/prompts to the last validated version or disable the faulty tool, and reduce autonomy. Resume only after relevant evals pass and the PM approves. Local stop/resume controls exist; disabling scheduled/intake work requires deployment integration. Do not claim reversal of external actions already taken.
- **Monitoring:** Track pass rate separately for EV-1–EV-6, escalation rate/reasons, estimated cost per run/day, duration, bound trips, blocked tool calls, and trust incidents. The PM reviews failures and near-misses weekly. Unsafe actions, leaks, or bypassed limits trigger immediate review and a pause. Current local logs provide inputs; automated evaluation metrics, alerting, dashboarding, and recurring production review are planned.

## ROI metrics (beyond adoption & tokens)

| Metric | Pilot target | Capture method |
|---|---|---|
| **Outcome — PM review readiness** | At least 90% of completed drafts accepted by the PM with only minor edits over a four-week pilot. Minor edits are wording/formatting only, not corrections to facts, confidentiality, priorities, or commitments. | PM labels approval and edit type for each draft. Track every run and report failures/escalations separately, alongside completion rate, so excluding incomplete work does not hide poor outcomes. This measures usable PM work, not merely draft generation. |
| **Cost-to-serve — Total cost per PM-approved update** | At least 25% below the manual baseline over four weeks, while staying within $0.10 estimated/run and $0.50 estimated/day. | Establish the manual baseline before the pilot. Include model/tool/platform spending, PM review/correction time at an agreed hourly rate, and failed/escalated-run costs in the numerator; divide by PM-approved updates. PM records review time and approval outcomes. |
| **Trust incidents** | Zero unauthorized writes, confidential disclosures, or bypassed limits over the four-week pilot. A critical incident pauses the pilot. | Maintain an incident log. Record missed required escalations and unsupported factual claims separately as near-misses, even when another control blocks the final action; apply the stricter clean-window rule above when assessing autonomy advancement. |

**Status:** These are approved pilot targets, not achieved results. The manual baseline, agreed hourly rate, PM outcome labels, and full measurement process must be established before the pilot. The current local spending gates are estimates, not exact provider billing ceilings.

## Widen-autonomy decision rule

Increase autonomy by one rung for a named segment only after the full four-week Trust Ladder gate passes, its clean incident window is satisfied, and the designated PM explicitly approves. Keep the Module 1 agent line unchanged; pause or reduce autonomy if a critical incident occurs.

## Governance & forward strategy

- **Compliance:** Exclude API keys, credentials, unnecessary personal data, and material outside the run's project/audience authorization. Redact before model calls; pause for the PM when access is unclear. This is the target policy: automatic redaction and source-level access controls are not implemented today and must be addressed before live use.
- **Safety:** Publishing, ticket/PR changes, launch-gate approval, and date commitments remain human-owned for every segment. The PM controls stopping/resuming; future writes require exact-action authorization. One passing demo never justifies widening autonomy. The current toolset has no external write capability; the local stop flag is cooperative and does not remotely cancel in-flight requests.
- **Reliability:** Keep 8 iterations, 2 revisions, a 90-second work deadline, $0.10 estimated/run, $0.50 estimated/day, and at most 10 proposed stories. Stop and preserve evidence when a limit or blocker is reached. If the model is unavailable, fall back to manual PM preparation: no fabricated update, silent model substitution, or automatic publication. The one-retry transient-source policy remains to be implemented. Current deadline/ledger controls are POSIX-main-thread and checkout-local; deployment must provide equivalent shared enforcement and account for their documented limitations.
- **Strategy:** Widen first into a read-only GitHub/Jira pilot for PM/operators. Defer researcher agents and executive direct use. Before pilot launch, name the PM and backup, implement scoped connectors and shared deployment controls, and pass connector-specific EV-1 (tool accuracy), EV-3 (recovery), EV-5 (jailbreak), and EV-6 (missing evidence) tests. This is a pilot-readiness prerequisite, not an autonomy promotion. Moving from assisted to supervised still requires the full four-week Trust Ladder gate and explicit PM approval.
