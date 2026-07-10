# Workflow Operacional

Este documento explica como central02, Acer, Codex, Gemini e Claude operam juntos no Task Cell Harness.

## Papéis

- `central02`: orquestrador central e PMO técnico. Mantém fila, estados, contratos, validações e scoreboard.
- `Acer`: worker de implementação. Executa a tarefa atribuída no estado atual, dentro do escopo permitido.
- `Codex`: executor assistido pelo ambiente local. Faz as alterações solicitadas, valida o resultado e prepara o relatório.
- `Gemini`: executor alternativo autorizado quando houver disponibilidade e contrato compatível com a Task Cell.
- `Claude`: executor alternativo autorizado quando houver disponibilidade e contrato compatível com a Task Cell.

## Fluxo de Trabalho

1. `central02` seleciona uma Task Cell na fila e confirma o estado atual.
2. `central02` define o objetivo da etapa e envia a tarefa ao worker apropriado.
3. `Acer` executa a etapa solicitada, normalmente `IMPLEMENTAR` neste ciclo.
4. `Codex`, `Gemini` ou `Claude` podem atuar como executores, conforme disponibilidade e contrato da Task Cell.
5. O executor designado aplica as alterações locais permitidas e mantém o trabalho restrito ao repositório.
6. `Acer` valida o resultado com os comandos solicitados e registra o retorno.
7. `central02` revisa o material em `VERIFICAR`.
8. Se aprovado, a tarefa segue para `DOCUMENTAR`, depois `PUBLICAR`, `REGISTRAR_SCOREBOARD` e `FINALIZADO`.
9. Se reprovado, a tarefa segue para `CORRIGIR` e obrigatoriamente volta para `VERIFICAR`.

## Regras Operacionais

- Não iniciar outra tarefa enquanto a atual estiver em execução.
- Não pular etapas do fluxo oficial.
- Não avançar de `CORRIGIR` diretamente para `DOCUMENTAR`.
- Não executar agentes reais automaticamente.
- Não integrar Tablet.
- Não iniciar a FASE 5.
- Não fazer commit ou push durante a execução da Task Cell.
- Substituições de executor devem ser registradas como exceção operacional.

## Responsabilidades por Etapa

- `PLANEJAR`: central02 define o recorte, as restrições e o plano de execução.
- `IMPLEMENTAR`: Acer, Codex, Gemini ou Claude produzem a alteração local conforme o executor designado.
- `TESTAR`: Acer executa validações locais autorizadas.
- `VERIFICAR`: central02 decide aprovar ou reprovar.
- `CORRIGIR`: Acer ajusta o trabalho com base no retorno da verificação.
- `DOCUMENTAR`: central02 consolida a documentação oficial aprovada.
- `PUBLICAR`: os artefatos aprovados são movidos para o estado canônico.
- `REGISTRAR_SCOREBOARD`: a linha de resultado é registrada.

## Resultado Esperado

Ao fim de uma Task Cell aprovada, o repositório deve refletir:

- documentação oficial consistente;
- relatório da execução;
- fixture JSON válido da Task Cell;
- rastreabilidade da etapa executada.
