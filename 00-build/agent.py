"""Cortex, a minimal, explicit agent loop you (and your coding agent) can read end
to end. This is the agent you ship: your PM chief-of-staff. You build it by
directing your coding agent (Claude Code / Cursor / Codex) to shape this file. You
never have to hand-write it.

Every bound the course talks about is visible right here in code, not buried in a
framework: the max-iteration counter, the cost cap, the revision cap, the
stop/escalate conditions, the auto-queue cap, and the absence of any publish tool.

Usage (ask your coding agent to run these for you, or run them yourself):
    python agent.py                # runs the happy-path task (weekly status update)
    python agent.py missing-data   # the stuck/escalate case
    python agent.py jailbreak       # the prompt-injection refusal case

Every run ends by showing the drafted status update in a FINAL STATUS UPDATE block
(or LAST DRAFT, held, if a bound trips), and saves it to run-output/. That file is
always a draft held for a human, it is never posted, there is no publish tool.

Requires OPENAI_API_KEY in your environment (see .env.example). Model and bounds
are read from env so you can tune them, that tuning is your M5 deliverable.

The loop is deliberately transparent (hand-written tool-calling on the openai
client) so a grader can see the machinery. Keep the bounds explicit if you rework it.
"""

from __future__ import annotations

import json
import os
import sys
import re
import time
import signal
import math
import threading
from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path

from openai import OpenAI

import tools
from critic import review
from daily_budget import DailyBudget, DailyBudgetBlocked, BudgetedClient
from prompts import CORTEX_SYSTEM

try:  # load .env if python-dotenv is installed; harmless if it isn't
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# --- Bounds (your M5 deliverable: tune these and justify them) ----------------
MODEL = os.environ.get("CORTEX_MODEL", "gpt-4o-mini")
MAX_ITERATIONS = int(os.environ.get("CORTEX_MAX_ITERATIONS", "8"))
MAX_REVISIONS = int(os.environ.get("CORTEX_MAX_REVISIONS", "2"))
COST_CAP_USD = float(os.environ.get("CORTEX_COST_CAP_USD", "0.10"))
MAX_QUEUE_ITEMS = int(os.environ.get("CORTEX_MAX_QUEUE_ITEMS", "10"))
RUN_TIMEOUT_SECONDS = float(os.environ.get("CORTEX_TIMEOUT_SECONDS", "90"))
DAILY_COST_CAP_USD = float(os.environ.get("CORTEX_DAILY_COST_CAP_USD", "0.50"))
# Rough $ per 1M tokens for your chosen model, set to match its pricing.
PRICE_IN = float(os.environ.get("CORTEX_PRICE_IN_PER_M", "0.15"))
PRICE_OUT = float(os.environ.get("CORTEX_PRICE_OUT_PER_M", "0.60"))

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "get_project", "description": "Look up a project by its ID (status, flags, linked PRD).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"}}, "required": ["project_id"]}}},
    {"type": "function", "function": {
        "name": "get_activity",
        "description": "Pull recent engineering activity for a project (merged PRs, open issues, Sev-1s).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"}}, "required": ["project_id"]}}},
    {"type": "function", "function": {
        "name": "search_past_updates",
        "description": "Search previous status updates and decisions for tone and precedent.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "get_roadmap",
        "description": "Return the roadmap. Some items are flagged confidential/embargoed.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "get_norms", "description": "Return the team norms / PM playbook the agent must follow.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "propose_stories",
        "description": "Queue a set of backlog stories for human approval (creates nothing; rejected above the item cap).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"},
            "stories": {"type": "array", "items": {"type": "string"}},
            "reason": {"type": "string"}}, "required": ["project_id", "stories"]}}},
]


class Bounds:
    """Tracks spend and trips the cost cap. This is enforced OUTSIDE the model."""

    def __init__(self):
        self.cost = 0.0

    def add(self, usage) -> None:
        self.cost += (usage.prompt_tokens * PRICE_IN
                      + usage.completion_tokens * PRICE_OUT) / 1_000_000

    def over_cap(self) -> bool:
        return self.cost >= COST_CAP_USD


OUTPUT_DIR = Path(__file__).parent / "run-output"


class OperatorStop(Exception):
    pass


def request_stop() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "STOP").touch()
    print("STOP requested. Runs sharing this checkout are blocked until explicit resume.")


def resume_runs() -> None:
    (OUTPUT_DIR / "STOP").unlink(missing_ok=True)
    print("STOP cleared. New runs are permitted; interrupted runs are not restarted.")


def check_operator_stop() -> None:
    if (OUTPUT_DIR / "STOP").exists():
        raise OperatorStop("operator stop flag set; explicit resume required")


def banner(text: str) -> None:
    print(f"\n{'=' * 64}\n{text}\n{'=' * 64}")


def emit_deliverable(which: str, draft: str, *, accepted: bool,
                     reason: str, cost: float) -> None:
    """Surface AND persist Cortex's drafted status update so it can't get lost in
    the scroll-back. This is still a DRAFT held for human review, never a post,
    there is no publish tool, and an escalated run is held on purpose.

    Runs on every exit: an accepted pass prints the FINAL update; a bound trip or
    escalation prints the LAST draft it managed to write plus why it was held.
    """
    banner("FINAL STATUS UPDATE (draft, validator-approved, NOT posted)" if accepted
           else "LAST DRAFT (held, NOT posted, escalated to a human)")
    if draft.strip():
        print(draft.rstrip())
    else:
        print("(Cortex stopped before it produced a draft, nothing to show.)")
    if not accepted:
        print(f"\nWhy it was held: {reason}")

    if draft.strip():
        OUTPUT_DIR.mkdir(exist_ok=True)
        out = OUTPUT_DIR / f"status-update-{which}.md"
        state = "accepted by validator" if accepted else "HELD, escalated"
        out.write_text(
            f"<!-- Cortex draft, {state}; NOT posted. Run cost ~ ${cost:.4f}. -->\n"
            f"<!-- {reason} -->\n\n{draft.rstrip()}\n", encoding="utf-8")
        print(f"\nSaved draft -> {out.relative_to(Path(__file__).parent)}  "
              f"(for your review, nothing was posted)")


def detect_permission_override(text: str) -> list[str]:
    """Conservative input guard for explicit override attempts, not a full detector.

    Matches trigger human review even in quoted material; no inferred permission
    from a task brief can disable this infrastructure check.
    """
    patterns = {
        "system/admin override": r"\bsystem\s+override\b|\badmin\s+mode\b",
        "ignore governing instructions": r"\bignore\s+(?:all\s+)?(?:previous|prior)\s+(?:rules|instructions|norms)\b",
        "suppress escalation": r"\bdo\s+not\s+escalate\b|\bdon['’]t\s+escalate\b",
    }
    return [label for label, pattern in patterns.items()
            if re.search(pattern, text, flags=re.I)]


class RunDeadlineExceeded(BaseException):
    """Bypass ordinary SDK exception/retry handling when the run deadline expires."""


def run(which: str = "happy") -> dict:
    """Enforce the overall work deadline in the POSIX CLI main thread."""
    if not hasattr(signal, "setitimer") or threading.current_thread() is not threading.main_thread():
        raise RuntimeError("Run deadline requires a POSIX main-thread process")
    if RUN_TIMEOUT_SECONDS <= 0 or not math.isfinite(RUN_TIMEOUT_SECONDS):
        raise ValueError("CORTEX_TIMEOUT_SECONDS must be positive and finite")
    if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
        raise RuntimeError("Cannot replace an existing process deadline")
    previous_handler = signal.getsignal(signal.SIGALRM)

    def expire(signum, frame):
        raise RunDeadlineExceeded()

    signal.signal(signal.SIGALRM, expire)
    try:
        # _run arms the timer after its evidence-saving closure is available.
        return _run(which)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def _run(which: str = "happy") -> dict:
    """Run one bounded task; every exit persists evidence and an explicit outcome."""
    started = time.monotonic()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    bounds = Bounds()
    task = tools.get_task(which)
    source_log = [task.get("body", "")]
    revisions = 0
    step = 0
    last_draft = ""
    verdict = None
    queued = []
    project_ids = set()
    retrieved = set()

    def finish(outcome: str, reason: str) -> dict:
        # End work before finalizing evidence; no new model/tools run from here.
        signal.setitimer(signal.ITIMER_REAL, 0)
        record = {
            "run_id": run_id, "fixture": which,
            "project_ids": sorted(project_ids), "outcome": outcome,
            "stop_reason": reason, "iterations": step, "revisions": revisions,
            "estimated_cost_usd": bounds.cost,
            "duration_seconds": round(time.monotonic() - started, 3),
            "limits": {"iterations": MAX_ITERATIONS, "revisions": MAX_REVISIONS,
                       "cost_usd": COST_CAP_USD, "queue_items": MAX_QUEUE_ITEMS,
                       "timeout_seconds": RUN_TIMEOUT_SECONDS},
            "daily_budget": {"limit_usd": DAILY_COST_CAP_USD,
                             "timezone": "America/Los_Angeles"},
            "draft": last_draft, "sources": source_log,
            "proposed_stories": queued, "critic": verdict,
        }
        OUTPUT_DIR.mkdir(exist_ok=True)
        record_path = OUTPUT_DIR / f"run-{run_id}.json"
        record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        banner(f"STOP: {outcome.upper()} — {reason}")
        emit_deliverable(which, last_draft, accepted=outcome == "success",
                         reason=reason, cost=bounds.cost)
        print(f"Run record -> {record_path.relative_to(Path(__file__).parent)}")
        print(f"Iterations: {step}; revisions: {revisions}; "
              f"cost ≈ ${bounds.cost:.4f}; duration: {record['duration_seconds']}s")
        return record

    if "error" in task:
        return finish("escalation", task["error"])

    banner(f"CORTEX RUN, fixture: task-{which} (auto-queue cap {MAX_QUEUE_ITEMS} items)")
    print(task["body"])
    override_signals = detect_permission_override(task["body"])
    if override_signals:
        last_draft = (
            "ESCALATE: Prompt-injection attempt flagged by input guard ("
            + ", ".join(override_signals)
            + "). Refused instructions to override permissions, publish restricted "
            "information, change tickets/launch gates, or commit dates. "
            "Human review is required; no model or task tool calls were made."
        )
        print(last_draft)
        return finish("escalation", "input guard: explicit permission override attempt")
    messages = [
        {"role": "system", "content": CORTEX_SYSTEM},
        {"role": "user", "content": f"PM task brief:\n\n{task['body']}"},
    ]
    wants_stories = bool(re.search(r"\bstor(?:y|ies)\b", task["body"], re.I))

    try:
        check_operator_stop()
        remaining = RUN_TIMEOUT_SECONDS - (time.monotonic() - started)
        if remaining <= 0:
            raise RunDeadlineExceeded()
        signal.setitimer(signal.ITIMER_REAL, remaining)
        client = BudgetedClient(
            OpenAI(max_retries=0),
            DailyBudget(OUTPUT_DIR / "daily-budget.json", DAILY_COST_CAP_USD, COST_CAP_USD),
            PRICE_IN, PRICE_OUT, before_call=check_operator_stop,
        )
        for step in range(1, MAX_ITERATIONS + 1):
            check_operator_stop()
            if bounds.over_cap():
                return finish("stuck", "cost cap reached")
            resp = client.chat.completions.create(
                model=MODEL, messages=messages, tools=TOOL_SCHEMAS)
            bounds.add(resp.usage)
            check_operator_stop()
            msg = resp.choices[0].message
            if bounds.over_cap():
                return finish("stuck", "cost cap reached after model response")

            if msg.tool_calls:
                messages.append(msg)
                for call in msg.tool_calls:
                    check_operator_stop()
                    fn = call.function.name
                    args = json.loads(call.function.arguments or "{}")
                    if fn not in {t["function"]["name"] for t in TOOL_SCHEMAS}:
                        return finish("escalation", "unapproved tool requested")
                    result = tools.TOOLS[fn](**args)
                    source_log.append(f"{fn}({args}) -> {json.dumps(result)}")
                    check_operator_stop()
                    print(f"\n[step {step}] TOOL {fn}({args})")
                    print(f"          -> {json.dumps(result)}")
                    if args.get("project_id"):
                        project_ids.add(args["project_id"])
                    messages.append({"role": "tool", "tool_call_id": call.id,
                                     "content": json.dumps(result)})
                    if result.get("error") or result.get("status") == "rejected":
                        return finish("escalation", f"{fn}: {result.get('error', 'rejected')}")
                    retrieved.add(fn)
                    if fn == "get_project" and (
                        result.get("status") == "embargoed"
                        or set(result.get("flags", [])) & {"confidential", "launch_hold"}
                    ):
                        return finish("escalation", "project confidentiality or launch hold needs human judgment")
                    if fn == "get_activity" and any(
                        str(item.get("severity", "")).lower() == "sev-1"
                        for item in result.get("activity", [])
                    ):
                        return finish("escalation", "open project Sev-1 needs human judgment")
                    if fn == "propose_stories":
                        queued.append(result)
                        if sum(batch["count"] for batch in queued) > MAX_QUEUE_ITEMS:
                            return finish("escalation", "cumulative story batch exceeds queue cap")
                continue

            last_draft = msg.content or ""
            print(f"\n[step {step}] PROPOSED OUTPUT:\n{last_draft}")
            # Escalation is a distinct exit, never critic-approved success.
            if re.search(r"^ESCALATE:", last_draft, re.M):
                return finish("escalation", "Cortex requested human judgment; output is held unvalidated")
            unmet = []
            if not re.search(r"^DONE:", last_draft, re.M):
                unmet.append("End with DONE or ESCALATE as instructed.")
            if not {"get_project", "get_activity", "get_norms"} <= retrieved:
                unmet.append("Retrieve the project, activity, and team norms before declaring done.")
            if wants_stories and not queued:
                unmet.append("Requested stories must have a successful propose_stories result.")
            banner("CRITIC, independent validation")
            verdict = review(client, MODEL, last_draft, "\n".join(source_log))
            bounds.cost += (verdict["_usage"]["prompt"] * PRICE_IN
                            + verdict["_usage"]["completion"] * PRICE_OUT) / 1_000_000
            print(json.dumps({k: v for k, v in verdict.items() if k != "_usage"}, indent=2))
            if bounds.over_cap():
                return finish("stuck", "cost cap reached after critic")
            if verdict.get("verdict") == "pass" and not unmet:
                check_operator_stop()
                banner("HITL CHECKPOINT — draft and proposals held for human review; nothing posted")
                return finish("success", "critic passed and completion requirements met")
            if revisions >= MAX_REVISIONS:
                return finish("stuck", f"draft still fails after {MAX_REVISIONS} revision attempts")
            revisions += 1
            print(f"\n-> revision {revisions}/{MAX_REVISIONS}")
            messages.append(msg)
            messages.append({"role": "user", "content":
                f"Validation failed: {verdict.get('reasons', [])}; {unmet}. "
                "Fix the draft or end with ESCALATE: and explain the human decision needed."})
        return finish("stuck", f"maximum iterations ({MAX_ITERATIONS}) reached")
    except KeyboardInterrupt:
        request_stop()
        return finish("stuck", "operator interrupted with Ctrl+C; explicit resume required")
    except OperatorStop as exc:
        return finish("stuck", str(exc))
    except RunDeadlineExceeded:
        return finish("stuck", f"overall run timeout ({RUN_TIMEOUT_SECONDS:g}s) reached; human review required")
    except DailyBudgetBlocked as exc:
        return finish("stuck", str(exc) + "; human review required")
    except Exception as exc:
        # Preserve evidence without writing credentials or raw exception payloads.
        return finish("stuck", f"runtime failure: {type(exc).__name__}; human investigation required")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else "happy"
    if command == "stop":
        request_stop()
    elif command == "resume":
        resume_runs()
    else:
        run(command)
