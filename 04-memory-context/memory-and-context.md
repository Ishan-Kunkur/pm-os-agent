# Context Engineering & Memory: Cortex PM Chief-of-Staff Agent

> Module 4 · Context Engineering & Memory
>
> ✅ **What this validates:** the agent reasons on the right, safe inputs, by the end you'll have proven a context budget, per-source retrieve-vs-long-context decisions, and a memory map with risk mitigations.
>
> 🗂️ **How the lab maps to this file:** In **Part A** (before the lecture) you don't edit this file, you rough-draft on scratch, focused on the per-source calls in **section 2** plus a quick remember/forget + "how it rots" sketch. In **Part B** (after the lecture) you complete **all five sections**; the Lab Guide's guided builder writes this file for you to copy in and commit.

## 1. Context budget

Prioritize context in this order:

1. Current approved norms and human-authority boundaries.
2. Complete task brief, project identity, and intended audience.
3. Current project activity and required PRD/roadmap evidence.
4. Relevant past updates and decisions.
5. Optional external research.

If space runs short, remove optional and older context first. If required evidence cannot fit or is missing, narrow retrieval or escalate; do not silently omit it. Source content is data and cannot override Cortex's rules.

**Implementation status:** This is the target context-priority design. The current loop accumulates its conversation and tool results; automated context trimming and token-budget enforcement are not implemented.

## 2. Retrieve vs. long-context: per source

For each data source, decide: **retrieve** (narrow a large/changing corpus to the relevant slice) or **long-context** (just include a bounded set you can reason over).

| Source | Size / volatility | Decision | Why |
|---|---|---|---|
| Recent GitHub/Jira activity (`get_activity`) | Growing, frequently changing records; small in today's fixture | Retrieve the relevant project and time window, retaining PR/issue IDs and metric provenance | Deciding factor: volatility. Each run needs current evidence. |
| Past updates and decisions (`search_past_updates`) | Archive grows over time | Retrieve relevant project history with dated, source-linked results | Deciding factor: size. The archive keeps growing. |
| Roadmap (`get_roadmap`) | Bounded project sections within a broader, changing roadmap; includes confidential flags | Retrieve the current authorized project section, then include that section in full | Deciding factor: citation/audit. Identify the exact roadmap version and section behind claims, preserving dependencies and confidentiality flags. |
| Team norms (`get_norms`) | Bounded approved document whose rules can change | Retrieve the current approved version each run, then include it in full | Deciding factor: volatility/currentness. The current rules govern what Cortex may do. |
| Task brief (`get_task`) | Small, bounded document for this run | Long-context: include the complete brief as task data | Deciding factor: small size. Splitting it could lose requirements; its contents cannot override Cortex's rules. |

**Implementation status:** The task brief is included in full today. Tools read local fixtures; activity is project-filtered but has no time-window filter, past-update search uses keyword overlap with a fallback that may include other projects, and roadmap/norms return their full files. Authorized project-scoped roadmap retrieval, versioned citations, and stronger history filtering are target behavior, not access controls already enforced by the runtime. Live GitHub/Jira connectors and external research remain planned.

## 3. Retrieval quality plan

| Retrieve source | Routing | Document grading | Reranking | Self-verification | Caching |
|---|---|---|---|---|---|
| Recent activity | Intended project and reporting period | Check project, dates, coverage, and retrieval success; missing activity must not mean no issues | Defer until volume requires prioritization | Trace each activity claim to a returned record before the draft advances | Skip initially: currentness is the deciding factor |
| Past updates and decisions | Intended project's history only | Check project, date, approval status, and relevance; reject unrelated fallback results | Prioritize relevance, recency, and whether newer decisions supersede older ones | Cite history as history, not as current facts | Not selected |
| Roadmap | Intended project's authorized section | Check version, currentness, audience permissions, and confidentiality flags | Not needed: include the selected section in full | Trace claims to the section; do not present planned work as completed | Defer until freshness rules are defined |
| Team norms | No additional routing selected for the current single-team document | Confirm the current approved version for the team | Not needed for the bounded document | Check the draft and proposed actions against the rules | Version-checked only: verify the approved version each run, reuse if unchanged, refresh otherwise |

Every retrieved source has document grading and self-verification to address its failure modes. The full task brief remains long-context input, not a retrieved corpus.

**Implementation status:** These are the approved retrieval-quality requirements. Today's fixture tools provide project lookup and basic keyword search; the independent critic checks claims against returned evidence, and the runtime requires activity retrieval before success. The withheld-activity probe showed the critic can still miss unsupported claims. Explicit coverage grading, time-window routing, approval/version checks, reranking, audience-aware section selection, and version-checked caching are not implemented yet. Selected moves are design requirements, not claims of reliable enforcement today.

## 4. Memory map (your PM brain)

| Memory type | What Cortex stores | Scope / TTL |
|---|---|---|
| **Working** (in-loop) | Task, project/audience scope, retrieved evidence, draft, story proposals, critic feedback, and counters | Run lifetime only. Clear active context when the run ends to prevent stale assumptions carrying forward; saved run records are governed separately and do not automatically feed future runs. |
| **Episodic** (past runs) | Run records for review, trend analysis, and recurring-problem investigation; approved updates and decisions distinguished from labeled drafts and failures | Retain for 90 days. Only human-approved updates and decisions may be retrieved as trusted history. Scope access by project and authorized audience. |
| **Semantic** (durable facts/prefs) | Approved team norms, preferences, and durable decisions with source/version information | Retain until superseded, with a 30-day review interval and currentness checks before reuse. Expire superseded or invalidated entries immediately. Retrieve live project status and roadmap information fresh rather than treating them as permanent facts. |
| **Shared** (across agents) | Approved task scope, necessary evidence briefs, source references, and explicit critic findings; no unrestricted shared conversation history | Run-scoped and project-scoped access, lasting until the run ends. Saved copies follow the separate 90-day episodic policy and do not automatically become trusted memory. |

**Implementation status:** These are the approved memory and retention rules. The current runtime keeps active context within one process and saves local run records; automatic deletion, 90-day retention enforcement, semantic review scheduling, approval-gated history retrieval, and specialist access controls are planned. Saved records are not automatically reused as context today.

## 5. Memory risks & mitigations

| Risk | Mitigation |
|---|---|
| **Drift** — Cortex treats its own suggestions as approved decisions, such as turning a proposed story into a confirmed priority in a later update | Keep drafts, proposals, and approved decisions explicitly labeled. Only human-approved records enter trusted memory. Preserve sources and approval history, and check retrieved claims against current evidence. Humans retain approval authority under the M1 agent line. |
| **Poisoning** — An issue, document, or saved record contains instructions to override rules or disclose restricted information | Treat retrieved content as evidence, never as authority to change permissions. Check source identity and approval status, keep suspect records out of trusted memory, and flag override attempts for human review. Only humans approve durable rule changes. |
| **Staleness** — Old updates describe completed work as upcoming or report an outdated metric, such as 41% when current activity says 43% | Refresh activity and roadmap evidence each run. Version-check norms before reuse, timestamp retrieved records, and mark superseded decisions. If current evidence is unavailable, say it cannot be verified and escalate rather than reuse old facts as current. |
| **PII, confidentiality, and retention** — Run logs retain sensitive task text and source records longer than needed or expose them outside the permitted project/audience | Collect only necessary information; redact unnecessary personal data and secrets before saving or sharing. Enforce project/audience access and keep sensitive records out of Git. Apply the 90-day episodic retention rule to saved run records, invalidate superseded semantic entries, and support authorized deletion. |

**Implementation status:** Run logs are gitignored, prompts reject permission overrides, and the runtime/critic provide partial grounding and escalation checks. Human-approved memory writes, source approval/version verification, enforced project/audience access, redaction, and automatic retention/deletion remain planned. The withheld-source probe demonstrated that current checks can miss unsupported claims; these mitigations describe requirements rather than complete enforcement. Carry the retention periods and access boundaries forward into M5 bounds and evals.
