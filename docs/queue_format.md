# Queue Format

## Purpose

The Task Cell Harness queue is represented by local task files under `tasks/`.
This keeps the queue inspectable, auditable, and portable without requiring a database.

## Current Queue Layout

The current harness uses these state directories:

- `tasks/pending/`
- `tasks/running/`
- `tasks/review/`
- `tasks/needs_revision/`
- `tasks/done/`
- `tasks/failed/`

Each task is represented by either:

- a directory containing `task.json`; or
- a legacy JSON file for backward compatibility.

## Canonical States

The architecture target for FASE 3.5 includes the following conceptual states:

- `created`
- `ready`
- `implementing`
- `implemented`
- `reviewing`
- `approved`
- `needs_changes`
- `failed`
- `archived`

These states are a conceptual queue model. The current scheduler and state machine already use a compatible operational mapping based on the harness workflow:

- `created` / `ready` map to pending work;
- `implementing` maps to running;
- `reviewing` maps to review;
- `approved` maps to done;
- `needs_changes` maps to needs_revision;
- `failed` maps to failed;
- `archived` is a future terminal state that may later map to a dedicated archival location.

## Permitted Transitions

The current state machine permits the following operational transitions:

- `pending` -> `running`
- `running` -> `review`
- `running` -> `done`
- `running` -> `failed`
- `review` -> `done`
- `review` -> `needs_revision`
- `review` -> `failed`
- `needs_revision` -> `pending`
- `failed` -> `pending`

The conceptual queue model should preserve these semantics unless a later phase explicitly extends them.

## Auditability

The queue remains auditable because task files are stored in plain JSON and the runner prints queue order deterministically.

## Compatibility Notes

This document does not change scheduler behavior.
It records the current operational mapping so later phases can evolve the queue format without breaking the existing harness.
