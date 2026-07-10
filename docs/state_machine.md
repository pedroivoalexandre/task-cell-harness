# Task Cell Harness State Machine

This document defines the official lifecycle for Task Cells in the Task Cell Harness.
It is the canonical state machine for the central02-led workflow.

## Official States

The official lifecycle states are:

- `BACKLOG`
- `READY`
- `PLANEJAR`
- `IMPLEMENTAR`
- `TESTAR`
- `VERIFICAR`
- `CORRIGIR`
- `DOCUMENTAR`
- `PUBLICAR`
- `REGISTRAR_SCOREBOARD`
- `FINALIZADO`

## Special States

The following states are valid and may be used to pause, stop, or retain a task outside the normal lifecycle:

- `BLOQUEADO`
- `AGUARDANDO_PEDRO`
- `CANCELADO`
- `ARQUIVADO`

## Allowed Transitions

### Main flow

| From | To |
| --- | --- |
| `BACKLOG` | `READY` |
| `READY` | `PLANEJAR` |
| `PLANEJAR` | `IMPLEMENTAR` |
| `IMPLEMENTAR` | `TESTAR` |
| `TESTAR` | `VERIFICAR` |
| `VERIFICAR` | `DOCUMENTAR` |
| `DOCUMENTAR` | `PUBLICAR` |
| `PUBLICAR` | `REGISTRAR_SCOREBOARD` |
| `REGISTRAR_SCOREBOARD` | `FINALIZADO` |

### Rejection flow

| From | To |
| --- | --- |
| `VERIFICAR` | `CORRIGIR` |
| `CORRIGIR` | `VERIFICAR` |

## Critical Rule

`CORRIGIR` never goes directly to `DOCUMENTAR`.
After any correction, the task always returns to `VERIFICAR` for a new approval pass.

## Special-State Use

Special states do not extend the main lifecycle flow. They are used when the task cannot continue normally:

- `BLOQUEADO`: the task cannot proceed without an external dependency or decision.
- `AGUARDANDO_PEDRO`: the task is waiting for Pedro's input or approval.
- `CANCELADO`: the task was stopped and should not continue.
- `ARQUIVADO`: the task is retained for reference and no longer actively worked.

## Invalid Transitions

Any transition not listed above is invalid and must be rejected.
Unknown states are also invalid.

## Operational Meaning

- `BACKLOG`: task registered but not yet ready for planning.
- `READY`: task is ready to be planned.
- `PLANEJAR`: scope, constraints, and approach are being defined.
- `IMPLEMENTAR`: local work is being executed.
- `TESTAR`: validations, checks, or tests are being run.
- `VERIFICAR`: central02 or the designated reviewer evaluates the result.
- `CORRIGIR`: implementation changes are being applied after rejection.
- `DOCUMENTAR`: final documentation is being produced after approval.
- `PUBLICAR`: approved artifacts are being published to the canonical location.
- `REGISTRAR_SCOREBOARD`: scoreboard entry is updated with the task result.
- `FINALIZADO`: the task is complete.

## Notes

- The task must not jump from `CORRIGIR` to `DOCUMENTAR`.
- The normal approval gate is always `VERIFICAR`.
- Special states can interrupt the lifecycle, but they do not replace the official main flow.
