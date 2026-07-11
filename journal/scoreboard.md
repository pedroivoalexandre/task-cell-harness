# Task Cell Harness — Scoreboard

Este arquivo é o painel operacional versionado das Task Cells acompanhadas pelo Central02.

O scoreboard resume o estado das tarefas, mas não substitui os contratos, relatórios, documentação ou commits Git.

## Política

- O Central02 é responsável por definir o estado oficial das Task Cells.
- Workers não alteram estados oficiais sem autorização do Central02.
- Cada entrada deve apontar para seus artefatos canônicos.
- Exceções operacionais devem registrar executor planejado, executor real, motivo e impacto.
- Commits e pushes só ocorrem quando autorizados.
- Este arquivo deve ser atualizado ao final de Task Cells relevantes ou quando o Central02 solicitar.

## Scoreboard atual

| Task Cell | Projeto | Estado | Resultado | Worker | Executor planejado | Executor real | Commit | Próximo estado |
|---|---|---|---|---|---|---|---|---|
| HARNESS-001 | Task Cell Harness | REGISTRAR_SCOREBOARD | Publicada | Acer | Gemini em TESTAR | Codex em TESTAR | `1c1f7e09ada3f8f58453f433faee6c76ed87d5c8` | FINALIZADO |
| APP-005 | App de Aprendizagem | REGISTRAR_SCOREBOARD | Publicada e aprovada | Acer | Codex em REGISTRAR_SCOREBOARD | Codex em REGISTRAR_SCOREBOARD | `ac0b1c1` | FINALIZADO |

## Registros detalhados

### HARNESS-001 — Definir a máquina de estados oficial do Task Cell Harness

- **Task ID:** `HARNESS-001`
- **Título:** Definir a máquina de estados oficial do Task Cell Harness
- **Projeto:** Task Cell Harness
- **Repositório:** `/home/vo/workspace/task-cell-harness`
- **Branch:** `main`
- **Estado atual:** `REGISTRAR_SCOREBOARD`
- **Resultado:** Publicada e aprovada
- **Worker:** Acer
- **Executor planejado:** Gemini em `TESTAR`
- **Executor real:** Codex em `TESTAR`
- **Commit:** `1c1f7e09ada3f8f58453f433faee6c76ed87d5c8`
- **Mensagem do commit:** `Publish HARNESS-001 documentation`

#### Artefatos publicados

- `docs/state_machine.md`
- `docs/workflow.md`
- `task-cells/HARNESS-001_state_machine.json`
- `reports/HARNESS-001_relatorio.md`

#### Exceção operacional

- **Estado:** `TESTAR`
- **Executor planejado:** Gemini
- **Executor real:** Codex
- **Motivo:** indisponibilidade operacional do Gemini CLI após erro de API e fallback de modelo
- **Impacto:** nenhum impacto no contrato da Task Cell

#### Riscos

- Baixo.
- Scoreboard criado como índice operacional, sem substituir relatórios ou Task Cells.

#### Pendências

- Nenhuma pendência funcional.

#### Próximo estado

`FINALIZADO`

#### Observações

- A HARNESS-001 foi implementada, testada, corrigida, verificada, documentada e publicada.
- O scoreboard registra o estado operacional resumido e aponta para os artefatos canônicos.

### APP-005 — Definir banco local de atividades em JSON

- **Task ID:** `APP-005`
- **Título:** Definir banco local de atividades em JSON
- **Projeto:** App de Aprendizagem
- **Repositório:** `/home/vo/workspace/projetos/app-aprendizagem`
- **Branch:** `main`
- **Estado atual:** `REGISTRAR_SCOREBOARD`
- **Resultado:** Publicada e aprovada
- **Worker:** Acer
- **Executor planejado:** Codex em `REGISTRAR_SCOREBOARD`
- **Executor real:** Codex em `REGISTRAR_SCOREBOARD`
- **Commit:** `ac0b1c1`
- **Mensagem do commit:** `Register APP-005 in scoreboard`

#### Artefatos publicados

- `docs/banco_local_atividades_json.md`
- `task-cells/APP-005_banco_local_atividades_json.json`
- `reports/APP-005_relatorio.md`

#### Riscos

- Baixo.
- Registro limitado ao scoreboard oficial, sem alterar o contrato da Task Cell.

#### Pendências

- Nenhuma pendência funcional.

#### Próximo estado

`FINALIZADO`

#### Observações

- A APP-005 foi registrada no scoreboard oficial do Task Cell Harness.
- O scoreboard registra o estado operacional resumido e aponta para os artefatos canônicos.
