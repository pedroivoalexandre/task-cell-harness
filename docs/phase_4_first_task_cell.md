# FASE 4 First Task Cell

## Task Summary

This Task Cell captures the first supervised local use of the harness in FASE 4.
The task is deliberately small and documentation-focused so the rollout remains easy to review and reverse.

## Objective

Define and document the safe local execution mode for FASE 4, including guardrails, approval requirements, and abort conditions.

## Context

FASE 3 proved that the harness can support a simulated implementation/review/report cycle.
FASE 4 now validates that the harness can support real local use under human supervision without autonomous dispatch or distribution.

## Inputs

- `docs/architecture_v2.md`
- `docs/task_cell_contract.md`
- `docs/orchestrator_cycle.md`
- `reports/phase_3_final_report.md`

## Constraints

- keep the work local to the harness repository;
- do not launch real agents automatically;
- do not integrate the Tablet;
- do not distribute work across machines;
- keep the change easy to roll back.

## Allowed Actions

- edit phase 4 documentation;
- create phase 4 task fixtures;
- write local reports;
- run local validation commands that do not require external agent execution.

## Forbidden Actions

- autonomous agent execution;
- parallel worker fan-out;
- Tablet integration;
- deploys;
- critical project modifications;
- unapproved Git write operations.

## Acceptance Criteria

- the phase 4 safety plan exists and is explicit;
- the phase 4 local execution mode exists and is explicit;
- the first task cell is represented as a stable JSON fixture;
- the execution and review flow are documented;
- the final report states the human decision and the phase boundary.

## Expected Artifacts

- `docs/phase_4_safety_plan.md`
- `docs/phase_4_local_execution_mode.md`
- `config/phase_4_execution_mode.json`
- `tasks/phase_4_first_real_task_cell.json`
- `reports/phase_4_first_execution_report.md`

## Implementer Prompt

Draft the phase 4 safety and local execution documentation, plus the first supervised task cell fixture. Keep the scope small, local, and reviewable.

## Reviewer Prompt

Review the phase 4 documentation and fixtures for completeness, guardrails, rollback clarity, and compatibility with the existing harness layout.

## Status

draft

## Report

`reports/phase_4_first_execution_report.md`
