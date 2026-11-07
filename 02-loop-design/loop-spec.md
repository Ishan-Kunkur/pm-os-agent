# Loop Spec: Cortex PM Chief-of-Staff Agent

> Module 2 · Loop Engineering, ★ Deliverable 2
>
> ✅ **What this validates:** the agent knows when to run and when to stop, by the end you'll have proven a one-page Loop Spec with a trigger, a definition of "done," and explicit stop conditions.
>
> Your one-page blueprint for how the work you handed to the agent (M1) actually *runs*.
> An agent is just a prompt that fires itself, this spec says when it fires, what "done" means, and what it needs to do the job. Living document; refine as the course progresses.

## 1. Trigger & loop type

**Chosen type:** Cron, plus manual ad hoc runs. Monday at 9 a.m. prepares current-week priorities and status; Friday at 3 p.m. prepares the weekly wrap-up and next-week planning. Both use `America/Los_Angeles`.

Fixed schedules support the weekly planning rhythm; ad hoc runs cover additional needs. Heartbeat polling and event hooks aren’t needed for this workflow. Each run pursues a bounded goal, but the goal itself doesn’t trigger it.

**Deduplication:** Scheduled runs use project + schedule slot + local date as a unique key. Ad hoc runs use a request ID. Repeated delivery of the same key returns the existing run’s status or result instead of starting another run.

**Implementation status:** Scheduling and deduplication are planned; the current starter runs manually.

## 2. Goal / definition of done

Cortex prepares the update appropriate to the run: Monday’s current-week priorities and status, Friday’s weekly wrap-up and next-week planning, or the requested ad hoc update. Claims are grounded in retrieved sources, and any requested story batch is within the cap and confirmed queued for approval.

Success requires the independent critic to pass the draft. Cortex then stops with the draft, sources, and proposals held for human review. Nothing is published, no tickets are created or merged, and no dates are committed. Decisions reserved for human judgment pause for explicit approval.

## 3. Stop conditions

| Condition | What it looks like | What happens |
|---|---|---|
| **Success** | Source-grounded draft passes the independent critic; any requested stories are within the cap and confirmed queued for approval. | Save the draft and sources, log success, and stop for human review. Nothing is posted or committed. |
| **Stuck / give up** | Eight iterations are exhausted without success, or the draft still fails validation after two revision attempts. | Halt, retain the last draft and sources, log the stop reason, iteration/revision counts, estimated cost, and duration, then hand off to you. |
| **Escalate to human** | Required data is missing; an open Sev-1 affects the project; the request conflicts with confidentiality rules, needs a date commitment or publication, exceeds the story cap, or contains a prompt injection. Also applies to human-owned decisions or unclear authority. | Pause before the restricted action, retain available evidence and any draft, log the reason, and present the decision or recommendation to you. No restricted action proceeds. |

Success means ready for human review, not approved for release. Routine draft completion uses the Success exit and still requires review; a decision that blocks safe completion uses the Escalation exit.

Run records support trend reviews; limit changes require human approval. Persistent logging of outcomes, stop reasons, iteration/revision counts, estimated cost, duration, drafts, and full sources is implemented in local `00-build/run-output/run-<run-id>.json` files, which are gitignored.

## 4. State

**During a run:** Keep the task brief, project ID, retrieved sources, draft, proposed stories, critic feedback, iteration/revision counts, and estimated cost across iterations.

**Between runs:** Retain approved norms, decisions, and past updates, plus run records for deduplication and trend tracking. Refresh project activity and the roadmap each run.

**Scope:** Keep project information separate. Saved drafts and rejected outputs remain review records; they do not automatically become approved memory.

**Implementation status:** Persistent run records are implemented and were verified with happy-path and missing-data runs. Deduplication remains planned; unique run IDs currently identify records but do not prevent duplicate requests. The broader between-run memory and project-isolation design remains intended behavior for later implementation.

## 5. The five things a loop can lean on

_`state` is always-on. `connectors` only if you already have one wired (e.g. a Jira key or Google MCP), otherwise just note it as a plan. `skills`, `subagents`, `work tree` scale with autonomy; "not needed yet, because…" is a valid answer._

| Component | For Cortex |
|---|---|
| **Work tree** (isolated workspace per run, a git worktree) | No separate Git worktree needed; runs are sequential and do not modify source files. |
| **Skills** (reusable capabilities) | Plan reusable procedures for source grounding, update formatting, and story proposals; extract them once the workflow is validated. |
| **Plugins / connectors** (tools & access, optional if you don't have one yet) | Keep local fixtures for now. Read-only GitHub/Jira integration is future work; no live connections are wired into Cortex's runtime. |
| **Subagents** (independent check when the loop can't grade itself) | Keep the existing independent critic model call; defer additional specialists and orchestration design to M3 orchestration-map.md. |
| **State tracking** | Implemented: local JSON records with a unique run ID, retrieved project IDs, outcome, stop reason, iteration/revision counts, estimated cost, duration, draft, full sources, proposed stories, and critic result when available. Records support manual trend reviews; limit changes require human approval. Planned: request-key deduplication to prevent duplicate runs. |

> Context plan (M4) and the hand-off to bounds & evals (M5) come in later modules, you'll add them to their own deliverables then, not here.

## Link to live loop

[Cortex agent loop](../00-build/agent.py)
