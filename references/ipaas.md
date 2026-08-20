# Playbook — iPaaS (Advanced Automations)

Use este playbook somente quando a integração estiver no `spec.md` aprovado. iPaaS é a camada de
fluxos que conecta Pipefy a sistemas externos; não confunda com automações nativas do pipe ou
agentes de IA.

## Pré-check e escopo

1. Confirme o connector Pipefy e o `pipe_id` que será dono do fluxo. Workspace, catálogo, flows,
   conexões e execuções são sempre escopados por pipe.
2. Rode `get_ipaas_tools(pipe_id)` para confirmar que iPaaS está habilitado e que o consultor tem
   permissão de criar automações nesse pipe. Se falhar por plano, feature desabilitada ou permissão,
   não tente contornar: registre a pendência com a mensagem devolvida pelo MCP.
3. Nunca carregue o catálogo inteiro no contexto. Para cada ação, descubra o catálogo compacto,
   expanda somente o `tool_name` que será usado e monte os argumentos a partir do `inputSchema`.

## Conexões

O builder trabalha em modo **reutilizar somente**. Antes de configurar passo que chama app externo,
use a tool de listagem de conexões do catálogo e confira se há uma conexão compatível.

Na porta C, o Planner faz esta pré-checagem de leitura antes da aprovação do spec, pois o pipe já
existe. Na porta B, o Builder a executa imediatamente após criar o pipe, antes de qualquer passo
externo. O toolkit também expõe `create_ipaas_connection` e a jornada OAuth correspondente, mas
essas tools ficam deliberadamente fora do escopo deste builder: lidam com credenciais e rotação de
segredos, e exigem um fluxo de autorização próprio.

- Havendo uma única conexão adequada, registre seu `externalId` no build e use-a.
- Havendo mais de uma, apresente as opções ao consultor; não escolha silenciosamente.
- Não havendo conexão adequada, não peça, aceite, armazene, crie nem rotacione credenciais. Registre
  no `changes.md` a conexão/piece necessária e deixe o fluxo como parcial até que o responsável a
  configure na UI ou por processo autorizado.
- Nunca copie segredo, token, URL OAuth de retorno ou conteúdo sensível para arquivos de handoff.

## Ciclo de vida do fluxo

1. **Descobrir.** Pesquise as pieces e leia os schemas de trigger, ações, conexões e opções que o
   spec exige. Use valores de opção, não rótulos, quando o catálogo os resolver.
2. **Construir rascunho.** Crie ou altere somente os flows e passos explicitamente aprovados no spec.
   Registre `flow_id`, trigger, pieces e status de validade retornado.
3. **Validar.** Rode a tool de validação do flow antes de qualquer teste ou publicação. Falha de
   validação deixa o item parcial; não publique.
4. **Testar.** Fluxo sem efeito externo pode ser testado após validação. Teste que possa enviar
   mensagem, gravar em sistema externo, criar registro ou disparar webhook exige aprovação explícita
   para aquele teste e dados descartáveis. Registre run id, entradas seguras, efeito esperado e
   resultado; não registre payloads sensíveis.
5. **Publicar.** Publicar/habilitar é uma aprovação separada da aprovação do spec e da aprovação de
   teste. Sem a autorização explícita de go-live, entregue o flow validado como rascunho pronto para
   publicação. Após publicar, releia o flow ou estado de execução para confirmar o status ativo.

## Falhas, retomada e segurança

- `call_ipaas_tool` pode executar mesmo quando há timeout ou erro de transporte. Nunca repita a
  chamada às cegas: leia o flow, a lista de runs ou o run retornado antes de decidir a retomada.
- Delete, retry, publish, enable e qualquer alteração em app externo exigem intenção explícita do
  consultor. Não use essas ações como tentativa de correção.
- Se uma integração cruzar pipes, fixe no spec qual `pipe_id` é dono do flow e quais pipes apenas
  recebem efeito. Não deduza o alvo pelo nome.
- A conferência estrutural checa somente o flow e seus estados no iPaaS; comportamento em sistema
  externo é evidência de teste funcional, não suposição.

## Entrega

Para cada integração, informe: nome e objetivo, pipe dono, `flow_id`, conexão reutilizada (sem
segredo), status de validação, evidência de teste quando houver, estado de publicação e qualquer
pendência humana. Link direto do flow/workspace só é informado quando a tool ou produto o retornar;
nunca invente URL.
