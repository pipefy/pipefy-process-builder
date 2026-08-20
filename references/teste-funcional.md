# Playbook — Teste funcional (opcional)

Etapa **sob demanda**, executada por um **subagente com contexto limpo em modelo Sonnet**. Só roda
quando o consultor pede. Vale quando o processo tem automação crítica, condicionais que gatilham
decisão, ou vai direto para produção.

A conformidade estrutural **já foi verificada** pela conferência (`conferencia.md` na pasta de
trabalho). **Não repita a auditoria estrutural** — se você varrer o pipe fase por fase, está
gastando 25 turns por algo que já está feito e registrado. Sua pergunta é diferente e complementar:
**o processo se comporta como deveria quando alguém usa?**

Você **não conserta nada**, nem "só esse campinho". Encontrou problema → registra. Consertar é do
Builder, no ciclo seguinte.

Leia antes: `handoff-schemas.md` (seções 1, 2 e 3) e `connector-rules.md`. Se o spec incluir
integração, leia também `ipaas.md`.

## Contexto de entrada
1. Pré-check de connector e acesso de leitura/escrita ao pipe (`connector-rules.md`, regra 1).
2. Leia da pasta de trabalho: `spec.md` (o comportamento esperado), `changes.md` (o "foco sugerido
   para o teste" indica onde quem construiu tem menos confiança — **priorize esses pontos**) e
   `conferencia.md` (o que já está verificado e o que ficou marcado como "não verificável nesta
   etapa" — essa lista é a sua pauta principal).
3. O `pipe_id` está no frontmatter do `changes.md`.
4. Para cada integração iPaaS, leia no spec o pipe dono, flow_id, efeito esperado e se a aprovação
   explícita para teste com efeito externo foi registrada. Sem essa aprovação, limite-se à evidência
   de validação/run já existente e marque o comportamento externo como não testável.

## Como testar

**Pipe novo ou clone-sandbox — teste livremente.** Crie um card de teste com título
`[TESTE] <slug do trabalho>` e exercite:

- **Caminho felizmente completo** — mova o card por todas as fases até uma fase `done`.
- **Pelo menos um desvio** — o caminho de exceção previsto no spec (reprovação, hold, devolução).
- **Obrigatórios** — tente avançar sem preencher campo obrigatório; tem que bloquear.
- **Condicionais** — preencha o campo-gatilho e confirme que o campo dependente aparece ou
  desaparece como especificado.
- **Automações observáveis** — as que produzem efeito verificável (movimento de card,
  preenchimento de campo, criação de card relacionado). Confirme o efeito, não a existência.
- **Agentes de IA** — só quando puderem ser acionados com segurança e sem consumo relevante.

Antes de mover, consulte `get_phase_allowed_move_targets` na fase atual: o workflow pode restringir
destinos, e uma tentativa barrada por regra do pipe não é falha do build.

**Se um card não move, diagnostique na ordem certa** antes de registrar falha: (1) há campo
obrigatório não preenchido na fase — **inclusive campo oculto por condicional**, que continua
obrigatório e trava o movimento sem erro visível? (2) o destino está entre os permitidos? (3) as
fases estão ligadas, ou o pipe ainda depende da configuração manual do fluxo? Só depois disso
considere problema de plataforma. Concluir "o conector está fora do ar" quando faltava preencher um
campo é um diagnóstico errado que interrompe o trabalho do consultor por nada.

**Título do card:** por default o Pipefy usa o primeiro campo como título, então o card de teste pode
aparecer com um título diferente do que você definiu. Isso não é falha — mas se o spec previa um
campo de título específico, confirme que `title_field_id` está configurado.

**Pipe vivo em produção (porta C, aplicação direta) — critério antes de ação.** Só execute um caso
funcional quando conseguir confirmar que o caminho **não dispara efeito externo**: e-mail a
fornecedor ou cliente, notificação a stakeholder, webhook, integração. Na dúvida, **não execute** —
registre o caso na seção "Não testável" para validação humana. Um e-mail disparado para o
fornecedor do cliente durante um teste é um incidente, não um bug encontrado.

**iPaaS — teste de flow.** Depois de validar o draft, fluxo autocontido pode ser testado e ter seu
run registrado. Flow que pode chamar app externo só é executado quando houver aprovação explícita
para aquele teste e dados descartáveis definidos no spec ou na autorização. Use o run retornado e
as tools de leitura de runs para conferir o resultado; não repita uma chamada após timeout nem use
retry sem intenção explícita. Nunca publique ou habilite flow como parte do teste.

## Saída
1. **Limpeza primeiro:** exclua ou arquive o card de teste e confirme no relatório. Card de teste
   esquecido em pipe de cliente é rastro que vira pergunta depois.
2. Escreva `test-results.md` na pasta de trabalho (formato na seção 3 de `handoff-schemas.md`,
   **sem** a seção de auditoria estrutural — ela vive no `conferencia.md`). Para iPaaS, registre
   flow_id/run_id, ação, efeito esperado, resultado e se o teste externo foi aprovado; nunca dados
   sensíveis ou payloads de terceiros.
3. `resultado: PASS` só se nenhum caso funcional falhou. Qualquer falha = `FAIL`.
4. Mensagem final ao orquestrador: PASS/FAIL, número de casos, número de falhas, uma linha por
   falha, e onde salvou o arquivo.

## Modo incremental (após correção)
Quando o orquestrador te passar uma lista de itens corrigidos, teste **somente os casos que tocam
esses itens**. Não refaça a bateria completa: um card de teste novo, os casos afetados, limpeza.
Registre no arquivo que foi rodada incremental e mantenha as falhas ainda abertas.

## Guardrails
- Nunca altere fase, campo, automação, condicional ou agente. Sua única escrita no pipe do cliente
  é o card de teste — e a remoção dele.
- Teste comportamento, não implementação. Verde suspeito (passou, mas o resultado parece errado)
  vai anotado para o review, não silenciado.
- Não invente caso de teste fora do spec. Se achar que falta cobertura, registre como observação.
- Siga `connector-rules.md`: tudo escopado por `pipe_id`, sem busca global.
- Não crie/rotacione conexão iPaaS, não publique/habilite flow e não execute teste externo sem a
  aprovação explícita exigida por `ipaas.md`.
