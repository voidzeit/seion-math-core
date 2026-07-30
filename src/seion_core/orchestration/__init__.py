"""Executable agent-graph-loop for the development lifecycle.

This turns the declarative spec in governance/DEVELOPMENT_LIFECYCLE.yaml,
governance/STATE_MACHINES.yaml, and governance/agents/*.yaml into a
deterministic, gate-checked executor: any agent (Claude, another tool, or
a human) drives a task through the 8 lifecycle stages via
`seion-core governance lifecycle {start,advance,status,list}`, with
required-evidence validation, a capped loop-back-on-verify-failure retry,
liveness-aware leases for concurrent sessions, and evidence logged into
the existing .ai/evidence/ledger.jsonl.

This is a deterministic gate/state-machine executor, not an autonomous
multi-agent dispatcher -- it never itself invokes an LLM or spawns a
sub-agent. See docs/orchestration/AGENT_GRAPH_LOOP.md.
"""

from __future__ import annotations
