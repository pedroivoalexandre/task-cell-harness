# Architecture V2

## Source Of Truth

GitHub is the official source of project state for the Task Cell Harness.
Local work on the Yoga is the development workspace used to evolve the harness before any broader rollout.

## Roles

### Lenovo Yoga

The Lenovo Yoga is the primary development environment for FASE 3.
All code changes, tests, documentation updates, and refactors are performed here.

### Galaxy Tab S10+

The Galaxy Tab S10+ is reserved for a future Control Plane role.
It may later coordinate monitoring, queue management, and task distribution, but it is not used in FASE 3.

### Acer and XPS13

The Acer and XPS13 are future worker nodes.
They are not part of the current execution model, but the architecture should remain portable enough for them to join later.

### Operations

Operations is a future oversight role for supervising the fleet, reviewing queue health, and coordinating releases.
It is not an execution role and does not replace source control.

## Task Cell Concept

A Task Cell is the unit of work handled by the harness.
It should carry:

- objective;
- implementation context;
- acceptance criteria;
- expected artifacts;
- implementation/review prompts;
- final report.

The harness should treat each Task Cell as a traceable unit that can be implemented, reviewed, and consolidated without requiring real external agents during FASE 3.

## Implementer / Reviewer Loop

The current operating model is a local implementer/reviewer loop:

1. create or receive a Task Cell;
2. generate an implementation prompt;
3. record implementation output;
4. generate a review prompt;
5. record review output;
6. consolidate the result;
7. produce a final report;
8. update the cell status.

This loop remains simulated or manual in FASE 3.
Real agent execution is explicitly prohibited in this phase.

## FASE 3 Boundary

FASE 3 is focused on making the harness robust, portable, and auditable before any distributed execution.

The phase includes:

- local artifact policy;
- automatic bootstrap of local runtime directories;
- removal of Python cache artifacts from tracking;
- documentation of architecture, contracts, queue format, and prompt/report templates;
- simulated local orchestration and end-to-end coverage.

The phase excludes:

- distributed execution;
- real agent orchestration;
- Tablet integration;
- production control-plane behavior;
- any change that would require networked agent execution.

## Criteria To Enter FASE 4

The project should only enter FASE 4 when all of the following are true:

- the harness is working cleanly in a fresh clone;
- local artifacts are handled by policy and bootstrap, not manual setup;
- core contracts and queue semantics are documented and testable;
- simulated orchestration is working end to end;
- no real agent execution is required to validate the harness;
- the repository is ready for future multi-node evolution without structural rework.

## Relationship To Artifact Policy

The local artifact policy defines what should be tracked and what should be ignored.
This architecture assumes that logs, caches, runtime state, and temporary outputs are local concerns unless explicitly promoted to canonical fixtures.

## Relationship To Directory Bootstrap

The local runtime bootstrap ensures that a clean clone can create required runtime directories automatically.
This removes manual `mkdir -p` preparation and makes runtime validation reproducible.

## Relationship To Cache Tracking Removal

Python cache files are generated artifacts, not source.
Removing them from tracking aligns the repository with the artifact policy and reduces noise in clones, tests, and future reviews.

## Operating Principles

- keep source of truth in GitHub;
- keep Yoga as the primary development worker;
- keep FASE 3 local, deterministic, and dry-run;
- preserve portability for later workers and platforms;
- prefer explicit contracts and documentation over implicit behavior.
