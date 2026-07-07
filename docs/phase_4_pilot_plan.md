# FASE 4 Pilot Plan

## Purpose

The pilot is a small, low-risk Task Cell chosen to validate real local use of the harness under supervision.
The pilot must stay inside the harness repository and must not require network access, Tablet integration, or distributed execution.

## Recommended Pilot Task

Pilot task:

- improve phase 4 documentation and fixtures for safe local execution;
- keep the scope limited to harness documentation, task cells, and reports;
- avoid production behavior changes;
- keep rollback simple.

## Why This Pilot

- the change is observable in source control;
- the rollback surface is small;
- the acceptance criteria are easy to check;
- the work is representative of the local supervised workflow;
- the task validates prompts, review, reporting, and traceability.

## Pilot Acceptance Criteria

- the safety plan is explicit;
- the local execution mode is explicit;
- the pilot task cell is documented;
- the first supervised task cell is represented as a fixture;
- the first execution report explains what was done and what was not done;
- the phase 4 final report clearly states the readiness decision.

## Pilot Constraints

- no automatic agent execution;
- no parallel workers;
- no Tablet;
- no distributed orchestration;
- no deploys;
- no changes outside the harness unless Central V2 explicitly approves them.

## Pilot Output

The pilot should produce:

- phase 4 documentation;
- phase 4 task cell JSON fixtures;
- phase 4 execution report(s);
- a final phase 4 recommendation.
