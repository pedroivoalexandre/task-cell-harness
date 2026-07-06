# Orchestrator Cycle

## Purpose

The orchestrator cycle is the local, simulated implementation/review/report flow for a Task Cell.
It exists to prove the harness workflow without executing real agents.

## Steps

1. receive or create a Task Cell;
2. generate an implementation prompt;
3. record a simulated implementation result;
4. generate a review prompt;
5. record a simulated review result;
6. produce a final report;
7. persist the resulting cell state.

## Constraints

- no real agent execution;
- no external CLI invocation;
- no network dependency;
- no Tablet integration;
- deterministic output suitable for tests.

## Local Artifacts

The cycle may write temporary implementation, review, and report files inside a local workspace.
These outputs should remain local unless explicitly promoted into canonical project assets.

## Compatibility

The cycle is designed to be used alongside the existing runner, queue, and report infrastructure without changing scheduler or state machine semantics.
