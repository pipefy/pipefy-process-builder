# Playbook — Porta D: ROI do processo

Duas etapas com autores diferentes: **coleta**, inline, pelo orquestrador (conversa com o consultor
+ leitura do pipe), e **cálculo**, por um **subagente de contexto limpo** (modelo default, não
Haiku), que só vê arquivos. Somente leitura no Pipefy. A porta D nunca estima: o que não vier do
pipe ou do consultor vira lacuna, e "ROI não calculável com segurança" é um resultado legítimo.

Leia antes: `handoff-schemas.md` (seções 8 e 9), `graphql-recipes.md` (§8.5–8.7), `connector-rules.md`
(§4.4 paginação, §4.5 semântica de log).

## Pré-requisito: o diagnóstico
A porta D parte do `diagnostico.md` da pasta de trabalho (As-is com ids, inventário de automações,
agentes e flows). Se não existir, rode a porta A primeiro — é ele que impede o cálculo de partir de
uma descrição inventada do processo. Não releia o pipe fase por fase.

## Etapa 1 — Coleta (orquestrador) → `roi-inputs.md`

### 1.1 Modo
Pergunte, com opções: **realizado** (o pipe roda em produção há pelo menos um período fechado e o
consultor tem dados do antes e do depois) ou **projetado** (processo novo ou recém-implantado — tudo
é estimativa e será rotulado como tal). O modo vai no frontmatter e em toda saída.

### 1.2 Métricas lidas do pipe (somente leitura, com fonte e limitação)
Colete o que der para ler, e registre a limitação ao lado de cada número:
- cards criados no período (`cards(pipe_id:, first: 50, after:)` filtrando por `createdAt` **do
  lado do cliente**, paginando — a API não tem filtro server-side por data; declare se foi
  amostra);
- execuções por automação em `automationLogsByRepo` paginado (§8.5) — **avaliadas, não executadas**
  (`connector-rules.md`, §4.5); `executionMetrics` pode vir zerado;
- runs iPaaS por flow (`ap_list_runs`, sucesso/falha);
- tempo por fase e ponta a ponta numa amostra de ≤ 50 cards (`phases_history`, §8.6);
- cards atrasados (`late`, `expired`) na amostra;
- inventário: automações, agentes, flows, templates (do `diagnostico.md`).
Contagem **não** é hora nem dinheiro. Converter "N execuções" em horas exige premissa do cliente
(minutos por execução) — sem ela, a métrica fica como contagem.

### 1.3 Premissas que só o consultor/cliente têm (pergunte, com o checklist do prompt)
- **Investimento total**: licença, horas de PS, integrações; valor, moeda, recorrente ou não. Valor
  em dólar exige o **câmbio informado** (valor, data, fonte) — nunca o câmbio "de hoje" buscado por
  conta própria.
- **Benefício**: se horas economizadas — quantas horas (ou minutos por execução/job) **e** o custo
  salarial/FTE de referência (ex.: R$ 6.000/mês) para converter; se outra fonte (receita, redução de
  custo direto) — valor e origem.
- **Período considerado**; **custos recorrentes e não recorrentes**.
Cada resposta entra com quem informou e quando. Opções selecionáveis ajudam a perguntar, mas o valor
é sempre o informado — nunca sugira um número como default.

### 1.4 Escrever `roi-inputs.md`
No formato da seção 8 de `handoff-schemas.md`. A seção **Lacunas** lista o que faltou. Se faltar
investimento, ou benefício, ou (para horas) o custo FTE, avise o consultor **antes** de disparar o
cálculo: o resultado será "não calculável" — ele decide se quer o arquivo mesmo assim.

## Etapa 2 — Cálculo (subagente) → `roi.md`

O orquestrador dispara um subagente **general-purpose**, modelo default, com um prompt que contém
apenas: "leia e siga à risca o playbook em `<caminho absoluto de references/roi.md>`, seção Etapa 2 e
Regras de cálculo", "você opera em somente leitura no Pipefy e **não estima nada**", o caminho
absoluto da pasta de trabalho e o de `references/`. Nada da conversa.

O subagente lê `roi-inputs.md` e `diagnostico.md`, aplica as **Regras de cálculo (verbatim)** abaixo e
escreve `roi.md` no formato da seção 9 de `handoff-schemas.md`. Devolve ao orquestrador: `status`,
ROI %, payback, e a lista de alertas — terso.

### Regras de cálculo (verbatim)

```text
Calcule o ROI deste case de forma assertiva, conservadora e auditável.
Use somente os dados fornecidos. Nunca invente, estime ou complete informações que não estejam disponíveis.
Antes de calcular, colete obrigatoriamente:

Investimento total (valor em dólar, a ser convertido para real)
Benefício financeiro gerado, incluindo:
Se o benefício vier de economia de horas de trabalho, informe:
Quantas horas (ou minutos por automação/job) foram economizadas
O custo salarial/FTE de referência usado para converter horas em valor financeiro (ex: R$ 6.000/mês)

Se o benefício vier de outra fonte (receita, redução de custo direto), informe o valor e a origem

Período considerado
Custos recorrentes e não recorrentes, se houver
Regras obrigatórias

Use somente os dados fornecidos. Nunca invente, estime ou complete informações ausentes.
Diferencie claramente entre economia de custo, ganho de produtividade, aumento de receita e horas/FTE economizados.
Não trate horas economizadas ou ganho de produtividade como dinheiro automaticamente. Só converta para valor financeiro se houver um custo salarial/FTE ou outro valor financeiro fornecido.
Não misture percentuais com valores absolutos.
Confira todas as unidades, períodos e moedas antes do cálculo.
Se houver dados inconsistentes, conflitantes ou insuficientes, pare o cálculo e sinalize exatamente o que precisa ser corrigido.
Não use projeções futuras como resultado realizado. Separe resultados reais de estimados.
Faça uma segunda validação matemática do resultado antes de apresentar a resposta.
Se a conversão de contagens (ex: automações executadas) em horas exigir uma premissa não fornecida pelo cliente, pare e peça esse dado. Não estime tempo por automação sem confirmação explícita.
Fórmula
ROI (%) = [(Benefício financeiro total − Investimento total) ÷ Investimento total] × 100
 Payback = Investimento total ÷ benefício financeiro mensal
Formato da resposta

Dados utilizados (com origem de cada valor)
Premissas (somente as explicitamente informadas)
Cálculo (fórmula com valores substituídos)
Resultado (investimento total, benefício financeiro, retorno líquido, ROI, payback)
Validação (checagem independente do cálculo)
Alertas (limitações, dados faltantes, arredondamentos, inconsistências)
Se não houver dados suficientes para um ROI confiável, responda "ROI não calculável com segurança" e explique o que está faltando.
```

### Complementos operacionais (não alteram as regras)
- **Modo `projetado`**: todo benefício é estimado por definição — o `roi.md` rotula cada valor como
  "estimado (informado por <quem>)" e o Resultado abre com "ROI projetado, não realizado".
- **Conversão de moeda**: só com `cambio_usd_brl` informado em `roi-inputs.md`; sem ele, o
  investimento em dólar fica em dólar e o cálculo para com a lacuna registrada.
- **Payback mensal**: benefício mensal = benefício do período ÷ meses do período, com o número de
  meses explícito no Cálculo.
- **Validação independente**: refaça o cálculo por caminho diferente (ex.: anual ↔ mensal) e mostre
  os dois números.

## Entrega (orquestrador)
Apresente no chat: modo, status, os três números (investimento, benefício, ROI/payback) **ou** a frase
"ROI não calculável com segurança" com a lista do que falta, e os alertas. Ofereça a porta E (deck com
o diagnóstico e este ROI). Nunca apresente o número sem o modo e sem os alertas.

## Guardrails
- Nada de escrita no Pipefy. Nada de estimativa, média de mercado ou "valor típico".
- Se o consultor pedir "só uma ordem de grandeza", a resposta é o modo projetado com as premissas
  dele registradas — nunca um número sem origem.
- Métrica do pipe é contexto e evidência de uso; só vira benefício com a premissa do cliente.
