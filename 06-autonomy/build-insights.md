# Build Insights: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 4, what you learned building it
>
> ✅ **What this validates:** you can reflect on what building it taught you, by the end you'll have proven the friction, the learning, and the aha that changes how you'd design your next agent.

## Friction

The biggest friction was discovering that a rule in a prompt was not an enforced boundary. Cortex sometimes missed an injection, invented facts, or received an incorrect critic verdict. We had to add controls outside the model—required-evidence checks, an input guard, deadlines, spending reservations, and stop/resume behavior—and test their failure paths.

## Learning

1. **Capability isn't permission:** Producing a draft doesn't authorize publishing or commitments.
2. **A critic is fallible:** It needs positive and negative tests, with failures preserved.
3. **The path matters:** Tool use, evidence, stop conditions, and human handoffs matter alongside the final answer.

## Aha moment

An agent's autonomy is defined by what the system permits and enforces, not by how confidently the model responds. The same unchanged jailbreak produced different behavior until a code-level guard made the explicit case deterministic.

## What you'd do differently

I would define the evidence contract and regression cases before polishing prompts: test missing sources, false metrics, injection attempts, and bound trips from the start. I would also scope retrieval by project before adding live connectors, and delay extra agents until their handoffs and budgets are clear.
