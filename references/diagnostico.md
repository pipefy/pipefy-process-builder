# Playbook — Diagnóstico (porta A)

Porta A, rodada **inline** na conversa principal. Você é um consultor sênior auditando um processo
que já existe. **Somente leitura: você não altera nada no Pipefy, em nenhuma hipótese.**

O diagnóstico é um entregável completo por si. Ele pode terminar em relatório e ponto — e com
frequência é isso que o consultor quer. Se ele quiser agir sobre os achados, ofereça seguir para a
porta C (evoluir), sem empurrar.

Leia antes: `graphql-recipes.md` (seção 1), `nomenclature.md` e `modeling_best_practices.md` (o
gabarito da conformidade), `brain-access.md` (grounding) e `connector-rules.md`.

Dois modos, conforme o que o consultor tem em mãos:

---

## Modo 1 — Auditar um pipe existente (o caso comum)

### 1. Leitura (2 a 3 chamadas, nunca mais)
Peça a URL ou o id do pipe. Rode a query `AuditPipe` de `graphql-recipes.md` (seção 1), a query de
automações **com a condição de disparo** (seção 5 — `get_automations` omite a condição, e diagnóstico
de automação sem ver a condição é chute) e, se houver, `get_ai_agents(repo_uuid=...)`. Está tudo lá:
fases, campos, condicionais com a fase em que estão ancoradas, movimentos permitidos, defaults de
segurança. **Nunca** varra `get_phase_fields` por fase.

### 2. Varredura de defeitos (faça isto primeiro)
É o achado de maior valor: coisas que estão **quebradas agora**, não só fora do padrão. Muitas
vezes o cliente ainda não percebeu — encontrar antes dele evita atrito e vira percepção de valor.
Procure explicitamente:

- **Condicional órfã, mal ancorada ou sem gatilho** — condicional numa fase cujo campo referenciado
  não existe ali, apontando para campo renomeado/excluído, ou **sem valor de comparação** (regra que
  nunca dispara). Muita condicional "existente" está no formulário inicial em vez da fase pretendida.
  Para detalhar a regra de uma suspeita, use `get_field_condition(<id>)` — só nas suspeitas.
- **Campo obrigatório escondido por condicional** — `required: true` em campo que alguma condicional
  esconde. Ele continua obrigatório e **trava o movimento do card sem erro visível**: o usuário não
  entende por que o card não anda. Defeito silencioso clássico, vale severidade alta.
- **Fase sem saída** — fase que não é `done` e não tem `next_phase_ids` nem movimento permitido: o
  card entra e não sai. Também o inverso: fluxo sem nenhuma fase `done`.
- **Automação apontando para o vazio** — fase de destino inexistente, campo de destino excluído,
  template de e-mail ausente, destinatário quebrado.
- **Automação desativada e esquecida** — `active: false` em regra que o processo pressupõe ativa
  (veja também `disabledReason`). E **automação sem condição** quando a lógica exige uma: só a query
  da seção 5 mostra isso.
- **Obrigatório travando automação** — campo obrigatório numa fase para onde uma automação move o
  card sem preencher esse campo.
- **Campo de prazo/SLA órfão** — campo de SLA ou data que nenhuma automação alimenta.
- **Select sem opções**, campos duplicados com o mesmo rótulo em fases diferentes sem razão,
  campos não editáveis que uma automação tenta preencher.
- **Agente de IA em estado indevido** — inativo quando deveria rodar, ou **ativo sem o cliente
  querer**: editar um agente religa o que estava desligado, então agente ativo consumindo crédito e
  agindo nos cards sem ninguém pedir é achado de severidade alta.
- **Segurança** — pipe público sem necessidade, `only_assignees_can_edit_cards` desligado,
  `only_admin_can_remove_cards` desligado, formulário inicial aberto além do previsto. Tudo isso é
  corrigível via API (`graphql-recipes.md`, seção 6), então entra como recomendação acionável.
- **Título do card** — se o pipe usa o primeiro campo como título automático em vez de um campo
  definido, os cards saem com títulos errados. `title_field_id` resolve.

### 3. Diagnóstico em três camadas
Depois dos defeitos, avalie o desenho. Cada achado vem com recomendação:

- **Conformidade** — contra `nomenclature.md` (nomes de pipe, fases, campos, automações,
  condicionais, e-mails, incluindo tags como `[Inativo]`, `[Auxiliar]`, `[Integração]`) e
  `modeling_best_practices.md` (número de fases, hide-all por fase, movimentos críticos por
  automação/botão em vez de arrasto, responsável por card, timezone em SLAs).
- **Alinhamento à BU** — consulte a base da BU do domínio no brain (`brain-access.md`): o que o
  padrão canônico faz e este pipe não faz, e o que ele faz que o padrão não prevê.
- **Oportunidades do brain** — 1 a 3 casos de clientes da mesma taxonomia: variações e agentes de
  IA que processos semelhantes usam com bom resultado.

### 4. Entrega
Escreva `diagnostico.md` na pasta de trabalho (formato abaixo) e apresente no chat um resumo
executivo: quantos defeitos por severidade, os 3 achados mais importantes e a pergunta se ele quer
transformar algo em plano de correção (porta C).

---

## Modo 2 — Avaliar a documentação do cliente antes de construir

Quando o consultor traz SOW, diagramas (BPMN ou formato próprio), matriz de responsabilidades ou
planilha do cliente e quer saber **o que ainda falta definir** antes de colocar a mão na massa.
Não há pipe para ler; a matéria-prima são os documentos.

1. Leia os documentos que ele apontar.
2. Consulte a base da BU do domínio no brain: ela é o gabarito do que um processo desse tipo
   precisa ter.
3. Produza o **relatório de lacunas**: para cada fase provável, o que já está definido e o que
   falta — regras de decisão, alçadas, campos e tipos, condicionais, responsáveis, SLAs,
   integrações, tratamento de exceção.
4. Seja franco sobre ambiguidade: documentação pouco padronizada (regra escondida em célula de
   planilha, condicional implícita em texto corrido) degrada muito o resultado de qualquer
   construção. Quando não conseguir extrair uma regra com confiança, **liste como lacuna e faça a
   pergunta objetiva** em vez de inferir. Inferência silenciosa aqui reaparece como retrabalho depois.
5. O valor desta entrega é paralelizar: enquanto o cliente levanta as pendências, o time avança no
   que já está claro. Diga isso explicitamente no fechamento.

---

## Formato do `diagnostico.md`

```yaml
---
trabalho: <slug da pasta>
modo: pipe | documentacao
cliente: <nome>
pipe_analisado: <id + url | n/a>
dominio: <ex.: Compras>
referencias_brain: [<documentos consultados>]
diagnosticado_em: <YYYY-MM-DD>
defeitos: <número>
---
```

1. **Resumo executivo** — 3 a 5 linhas: estado geral e o que exige ação imediata.
2. **Defeitos encontrados** — tabela: `# | Severidade (Crítico/Alto/Médio/Baixo) | Onde (fase/
   campo/automação + id) | O que está errado | Impacto para o usuário | Correção recomendada`.
   Ordenada por severidade. No modo documentação, esta seção vira **Lacunas**.
3. **Conformidade** — tabela: `Item | Situação | Referência (nomenclatura/best practice) |
   Recomendação`. Só o que está fora do padrão.
4. **Alinhamento à BU** — o que falta e o que sobra em relação ao padrão canônico do domínio.
5. **Oportunidades** — variações e agentes de IA de casos semelhantes do brain, com o caso de
   referência citado.
6. **As-is** (só modo pipe) — estrutura normalizada no formato das seções 2 a 6 do spec (fases,
   campos, automações, condicionais, agentes, com ids reais). É o que permite virar plano de deltas
   na porta C sem reler o pipe.

## Guardrails
- **Nada de escrita no Pipefy.** Nem card de teste, nem rótulo, nem "só ativar essa automação".
  Se o consultor pedir correção durante o diagnóstico, ofereça a porta C — não corrija aqui.
- Severidade é sobre impacto no usuário do processo, não sobre elegância do modelo.
- Não invente padrão: o que não estiver na BU nem em caso do brain, rotule como sugestão sua.
- Disciplina de custo: 2 a 3 chamadas para ler o pipe, 1 a 3 documentos do brain. Nunca despeje
  a base inteira nem varra fase por fase.
