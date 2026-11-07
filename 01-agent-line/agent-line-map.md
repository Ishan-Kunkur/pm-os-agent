# Agent Line Map: Cortex PM Chief-of-Staff Agent

> Module 1 · The Agent Line
>
> ✅ **What this validates:** every risky action has a clear owner, by the end you'll have proven an above/below-the-line map with HITL checkpoints, scored on reversibility, blast radius, and measurability.

## The workflow, decision by decision

List every discrete decision or action in your agent's workflow, then score each one and place it **above** the line (a human owns it) or **below** (the agent owns it). Borderline calls get an HITL checkpoint.

| Decision / action | Reversibility (H/M/L) | Blast radius (H/M/L) | Measurability (H/M/L) | Above / Below | HITL? |
|---|---|---|---|---|---|
| Pull project state + activity | H | L | H | Below | No per-retrieval approval |
| Decide relevant context | H | L | M | Below | Required review |
| Draft the update | H | L | H | Below | Approval before sharing; none to create the draft |
| Decide tone/commitment level | L | H | M | Above | Human decides |
| Flag at-risk items | H | L | M | Below | Required review |
| Choose what to escalate | M | H | M | Above | Human decides |
| Propose a capped story batch | H | L | M | Below | Required approval |
| Post an update | L | H | M | Above | Human posts |
| Approve a company-wide update | L | H | M | Above | Human approves |

## Agent anatomy (sketch)

- **Model:** Use `gpt-4o-mini` for routine drafts. Escalate difficult cases to me; I decide whether a stronger model is needed, keeping costs predictable and retaining control over difficult judgments.
- **Tools:** Keep the current read tools and capped story proposals for human approval. Publishing, ticket/PR changes, and date commitments remain human-owned. Future capability: Cortex may execute specific actions only after explicit human approval enforced in code; changes to the approved action require fresh approval.
- **Memory:** Retain approved team norms, decisions, and past updates. Retrieve current project activity and the latest roadmap each run. Saved drafts remain review artifacts and are not automatically reused as memory, reducing the risk of carrying forward unapproved or stale information.
- **Loop:** _placeholder, defined in M2 loop-spec.md_
- **Bounds:** _placeholder, defined in M5 bounds-and-evals.md_
- **Evals:** _placeholder, defined in M5 bounds-and-evals.md_

## The golden rule, applied

1. Pulling project state and activity sits below the line because mistakes are easy to reverse, the blast radius is low, and the retrieved data is easy to verify; the deciding factor is high measurability.
2. Selecting relevant context sits below the line with required human review because the selection is easy to change and has a low blast radius, but omissions are harder to detect; the deciding factor is medium measurability.
3. Drafting the update sits below the line because the draft is easy to edit or discard, has a low blast radius before sharing, and its claims are easy to verify; the deciding factor is high reversibility.
4. Deciding tone and commitment level sits above the line because communicated commitments are hard to reverse, can affect many downstream decisions, and require judgment to verify; the deciding factor is high blast radius.
5. Flagging at-risk items sits below the line with required human review because flags are easy to correct and have a low blast radius, but missed risks are harder to detect; the deciding factor is medium measurability.
6. Choosing what to escalate sits above the line because a missed escalation may cost response time that cannot be recovered, can affect downstream decisions, and requires judgment to verify; the deciding factor is high blast radius.
7. Proposing a capped story batch sits below the line with required human approval because proposals are easy to change, have a low blast radius before approval, and require judgment to assess their usefulness and priority; the deciding factor is medium measurability.
8. Posting an update sits above the line because readers’ actions cannot be fully reversed, incorrect information can have a high blast radius, and downstream effects take judgment to assess; the deciding factor is high blast radius.
9. Approving a company-wide update sits above the line because its release is hard to reverse, incorrect information can affect the whole organization, and its suitability requires judgment to assess; the deciding factor is high blast radius.

## Hardest call

Deciding relevant context was my hardest call. Cortex can select information for a draft, but important omissions are harder to detect than incorrect included facts. Measurability settled it: Cortex owns the selection, with visible sources and required human review before sharing.
