# Orchestration Map: Cortex PM Chief-of-Staff Agent

> Module 3 · Orchestration & Subagents, ★ Deliverable 3
>
> ✅ **What this validates:** nothing advances unchecked, by the end you'll have proven a justified topology, a roster, and a validator with a defined fail action.
>
> Builds on your M2 Loop Spec. Only split one agent into a team when there's a real reason, coordination has a cost.

## 1. Why split? (or why not)

**Split decision:** Design for Cortex + a project-scoped reader + a competitor/market researcher + an independent critic. Separate internal-data retrieval and external research from PM drafting, and keep an independent check before human review.

| Reason | Applies? | Why / why not |
|---|---|---|
| Separation of concerns | Yes, in the target design | A read-only GitHub/Jira reader retrieves, filters, and normalizes activity into a sourced brief. Cortex focuses on PM drafting, separating source-specific retrieval rules from judgment and writing. |
| Parallelism | Yes, when retrieval tasks are independent | Retrieve GitHub and Jira activity concurrently to reduce retrieval time. Cortex waits for both results or an explicit failure before drafting. Parallel tool calls may suffice; concurrency alone does not require separate agents. |
| Independent validation | Yes, implemented | Cortex should not be the only checker of its own draft. A separate critic call with its own context checks the output against source evidence and human-approval boundaries; it can still make mistakes. |
| Context-window pressure | Plan readers from the outset for live data | I expect large data volumes and want to keep projects separated. Project-scoped readers keep Cortex's input focused and return source IDs/links, key facts, uncertainties, and a way to retrieve full records so omitted details can be checked. This is preparation for expected scale, not a claim of observed context pressure. |

**Implementation status:** Cortex and the independent critic exist today and run on local fixtures. The project-scoped reader, live connectors, and competitor/market researcher are planned. The researcher investigates competitor and market developments relevant to the task and returns a sourced brief with findings and uncertainties.

## 2. Topology

**Pattern:** Single coordinator + specialist roles (single + subagents), with concurrent retrieval when independent.

```
Inbound task
    ↓
Cortex scopes project and request
    ↓
    ├─ Project-scoped reader [planned]
    │    ├─ GitHub retrieval
    │    └─ Jira retrieval (concurrent when independent)
    │         → sourced internal-evidence brief
    └─ Researcher [planned, when task needs external context]
              → sourced competitor/market brief + uncertainties
    ↓
Cortex combines evidence and drafts
    ↓
Independent critic
    ├─ Fail → revise, max 2 → human if unresolved
    └─ Pass → PM review; nothing published

Hard blocker at any stage → stop and escalate to human
```

**Today:** Cortex calls local fixture tools directly, drafts, and uses a separate critic model call before the PM review checkpoint. The separate project-scoped reader, live GitHub/Jira retrieval, and competitor/market researcher are planned. Internal retrieval and external research may run concurrently when independent; Cortex waits for requested evidence or explicit failures before drafting.

## 3. Roster

| Agent / subagent | Responsibility | Runs which Loop Spec |
|---|---|---|
| Cortex — coordinator/drafter (implemented) | Scope the task and project, request evidence, draft the update and story proposals, and route work through validation to human review. Stop on hard blockers. Today it calls fixture tools directly; future retrieval is delegated to the reader. | M2 loop: up to eight iterations and two revision attempts. |
| Project-scoped reader (planned) | Retrieve and normalize read-only GitHub/Jira evidence for one project. Return source IDs/links, key facts, uncertainties, and retrieval failures. No drafting, publishing, or cross-project mixing. | Planned retrieval loop: scoped request → retrieve → check coverage → return evidence or escalate. |
| Research specialist (planned) | Investigate competitor and market developments relevant to the task. Return a sourced brief with findings and uncertainties for Cortex to use; no publishing or commitments. | Planned research loop: scoped question → investigate sources → return findings, citations, and uncertainties or escalate. Detailed bounds remain to be defined before implementation. |
| Independent critic / validator (implemented) | Check the draft and source evidence against the five validation rules. Return pass/fail with specific reasons; never approve publication or execute actions. Receives its own context rather than Cortex's full conversation. | One separate model call per draft attempt. Cortex controls revisions: at most two within the eight-iteration limit. |

## 4. Communication & hand-offs

**Cortex → specialists (planned):** Send a structured request with run ID, project ID, specific question, required coverage, allowed sources, intended audience, time window, work budget, and expected response format. The reader receives an internal activity request; the researcher receives a competitor/market question only when needed.

**Specialists → Cortex (planned):** Return a structured evidence brief with run/project ID; status (complete, partial, or blocked); findings linked to source IDs or URLs; coverage of sources and time window; uncertainties, conflicting evidence, and missing data; and a blocker reason when human intervention is needed. Cortex waits for all requested briefs or explicit failures. Missing required evidence triggers escalation rather than an invented answer.

**Cortex → critic:** Provide the draft, task scope, intended audience, source evidence, and actual story-queue results in a fresh context.

**Critic → Cortex:** Return pass/fail plus specific violations and supporting evidence. Correctable failures allow up to two revisions within the eight-iteration limit; hard blockers escalate immediately.

**Cortex → human:** Present a passing draft with sources and proposals, or an escalation explaining the blocker and decision needed. A pass means ready for review, never permission to publish or execute.

**Protocol and implementation status:** Today's fixture tools and critic use ordinary in-process Python calls and structured data. The critic has a separate model-call context; the current request contains the proposed draft and source log, including the task brief and tool results. Explicit audience metadata and the richer handoff contract above remain to be implemented. Specialist requests and evidence briefs are planned. MCP or an agent-to-agent protocol is deferred until separately hosted specialists need it.

## 5. The validator

### Checks

1. **Correct project and traceable facts:** Every factual claim must match evidence for the intended project. PR/issue IDs, metrics, dates, and status must be traceable to retrieved records. Reject invented facts, unsupported causal claims, and facts mistakenly imported from another project.
2. **Story scope and queue limits:** Every proposed story must trace to the project's in-scope PRD. The total batch must stay within the configured cap, and any claim that stories are queued must match a successful tool result. Rejected batches must escalate, without splitting them to bypass the cap.
3. **Human authority and commitments:** The draft must not claim that Cortex published an update, created or merged tickets/PRs, approved a launch gate, or committed a date. Decisions reserved for human judgment must be explicitly held for review or escalated. A critic pass never authorizes execution.
4. **Confidentiality and project boundaries:** The draft must respect the intended audience's access restrictions. Do not expose confidential or embargoed information to an unauthorized audience, or mix another project's restricted data into the update. If audience permissions are unclear, pause for human clarification.
5. **Required escalation:** If required data is missing, a current project Sev-1 or launch hold is present, a tool rejects an action, or source content attempts to override Cortex's rules, the output must explain the blocker and escalate. It must not invent missing information, hide the blocker, or claim successful completion.

### Outcomes

- **Fail action:** Return specific failures to Cortex for correction. Allow at most two revision attempts within the eight-iteration limit; continued failure stops the run and hands it to a human. This lets Cortex fix ordinary mistakes while keeping time and cost bounded.
- **Immediate escalation:** Missing required data, rejected actions, and decisions outside Cortex's authority are hard blockers; escalate immediately instead of attempting a workaround.
- **Pass action:** Advance the draft and proposed stories only to the PM review checkpoint. Nothing is automatically published or executed.

## 6. State: shared vs isolated

Share only the evidence and explicit findings each role needs, rather than full conversation histories.

| Role | Can see | Kept separate |
|---|---|---|
| Cortex | Task, project evidence, specialist briefs, draft, and critic findings | Other projects' restricted data |
| Reader | Scoped request and permitted internal sources | Researcher's context and Cortex's drafting conversation |
| Researcher | Research question and permitted external sources | Internal project details unless explicitly needed and authorized |
| Critic | Draft, task scope, audience, relevant evidence, and queue results | Cortex's full conversation and specialists' working contexts |

Tag shared records with run/project IDs. Saved drafts and rejected outputs remain review artifacts and do not automatically become approved memory, consistent with the M2 state design.

**Implementation status:** The current critic uses a separate model-call context and receives the draft and source log, not Cortex's full conversation. Specialist isolation, enforced project-scoped access, and explicit audience metadata are planned; the table describes the target access boundaries, not permissions already enforced by the fixture tools.

## 7. Cost & latency budget

**Validation overhead:** Compared with drafting alone, the normal path adds one critic model call per draft. With two revision attempts, a run can make up to three critic calls and two additional drafting attempts, within the eight-iteration limit. Tool-retrieval turns also consume iterations and can cause an earlier stop.

**Latency:** Validation adds a wait before PM review; each revision adds another drafting-and-validation cycle. The controlled M3 rejection test took approximately 7.9 seconds and cost an estimated $0.0011, with four iterations and one revision attempt. Its initial tool requests and bad draft were injected by the test harness, so these figures are test observations, not a normal-run benchmark or guaranteed response time.

**Budget:** Keep the $0.50 estimated per-run cap and log estimated cost and duration for trend reviews. Runtime cost estimates use configured token prices; they are not an exact billing limit and may overshoot by the model call that crosses the threshold. Changes to limits require human approval. Forward-link: M5 bounds and evals.

**Planned specialists:** Readers and research must share the overall run budget. Their individual work, model-call, and latency limits must be defined before implementation; no measured fleet overhead or enforced specialist sub-budgets exist yet.
