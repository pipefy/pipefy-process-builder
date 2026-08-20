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

O builder trabalha em modo **reutilizar somente**. Antes de configurar qualquer passo, levante
**todas** as conexões exigidas pelo flow — inclusive a conexão Pipefy do trigger, além das conexões
dos apps externos — e use a tool de listagem de conexões do catálogo para conferir se há uma
conexão compatível para cada uma.

Na porta C, o Planner faz esta pré-checagem de leitura antes da aprovação do spec, pois o pipe já
existe. Na porta B, o Builder a executa imediatamente após criar o pipe, antes de qualquer passo
externo. O toolkit também expõe `create_ipaas_connection` e a jornada OAuth correspondente, mas
essas tools ficam deliberadamente fora do escopo deste builder: lidam com credenciais e rotação de
segredos, e exigem um fluxo de autorização próprio.

- Havendo uma única conexão adequada, registre seu `externalId` no build e use-a.
- Havendo mais de uma, apresente as opções ao consultor; não escolha silenciosamente.
- Não havendo conexão adequada, não peça, aceite, armazene, crie nem rotacione credenciais. Registre
  no `changes.md` a conexão/piece e a finalidade necessárias, deixe somente esse item como parcial e
  dê o link acionável `https://app.pipefy.com/pipes/<pipe_id>/integrations` para o responsável
  configurá-la na UI ou por processo autorizado. Sem todas as conexões requeridas, não construa um
  flow "mock" como se ele funcionasse: entregue o blueprint dos passos e mapeamentos para retomada.
- Nunca copie segredo, token, URL OAuth de retorno ou conteúdo sensível para arquivos de handoff.

## Ciclo de vida do fluxo

1. **Descobrir.** Pesquise as pieces e leia os schemas de trigger, ações, conexões e opções que o
   spec exige. Use valores de opção, não rótulos, quando o catálogo os resolver.
1.5 **Comprovar a origem dos data pills.** A regra vale para **todo** valor `{{...}}` que venha do
   trigger ou da saída de qualquer step anterior, não apenas para o trigger. Para cada expressão,
   registre se ela vem de (a) schema real do pipe/campo, (b) schema ou documentação da piece/action,
   ou (c) amostra segura de execução. Campos Pipefy podem ser mapeados a partir da estrutura real do
   pipe; isso não autoriza inferir o envelope da piece. Quando o caminho exato não estiver provado
   pelo schema/documentação disponível, marque-o `shape_unverified` e pergunte ao consultor se pode
   executar um teste controlado com card/evento para confirmá-lo. Não é obrigatório testar por rotina
   quando a fonte já for comprovada; se o teste disparar escrita, mensagem ou outro efeito externo,
   ele continua sujeito à aprovação específica e a dados descartáveis. Nunca publique flow que ainda
   tenha expressão `shape_unverified`.
2. **Construir rascunho.** Crie ou altere somente os flows e passos explicitamente aprovados no spec.
   Registre `flow_id`, trigger, pieces e status de validade retornado.
3. **Validar.** Rode a tool de validação do flow antes de qualquer teste ou publicação. Falha de
   validação deixa o item parcial; não publique. `ap_build_flow` ou `ap_validate_flow` aprovado
   comprova somente a configuração estrutural dos steps, não que uma expressão `{{...}}` resolve no
   payload runtime; use o estado de comprovação dos data pills para deixar isso explícito.
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
segredo), situação dos data pills (`shape_verified` ou `shape_unverified`), status de validação,
evidência de teste quando houver, estado de publicação e qualquer pendência humana. Para conexão
ausente, informe o link de integrações do pipe; link direto do flow/workspace só é informado quando
a tool ou produto o retornar, nunca invente URL.
