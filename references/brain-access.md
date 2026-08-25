# Acesso ao brain — conhecimento de referência

O conhecimento que ancora o discovery vive no **Pipefy Brain** e é lido pelo conector
**"Pipefy Brain (Corporate)"** (MCP), que todo consultor do time tem ativo no Claude Code.
Duas fontes, dois papéis:

| Fonte | Papel |
|---|---|
| **Base da BU** (bu-standards) | O **default** — padrão canônico por domínio. Em conflito, a BU vence. |
| **Casos de clientes** (blueprints) | O **menu de variações** — benchmarks de clientes reais da mesma taxonomia. |
| **Padrões de integração** (iPaaS blueprints) | Opcional — referência de desenho (trigger, steps, mapeamentos) por app/piece já resolvido antes. Pode não existir ainda; ausência não bloqueia nada. |

## Pré-check do conector

Antes do grounding, confirme que o conector **Pipefy Brain (Corporate)** está disponível na
conversa (procure as ferramentas dele; se estiverem em lista deferida, carregue-as via
ToolSearch). Se o conector não estiver ativo: **avise o consultor** para ativá-lo no Claude
Code e siga com julgamento consultivo, deixando explícito no spec o que ficou sem grounding.
Não trave o fluxo.

## Como ler (ordem obrigatória, econômica)

As ferramentas exatas do conector podem variar (busca, listagem, leitura de documento) —
descubra-as em runtime e use a que melhor casa com cada passo. O que não varia é a disciplina:
**nunca despeje a base inteira no contexto** — busque, selecione poucos documentos e leia só esses.

1. **Base da BU primeiro.** Busque no brain o padrão da BU (bu-standards) para o **domínio**
   do pedido (ex.: Procurement/Compras) e leia o(s) documento(s) canônico(s). Essa é a espinha
   do processo.
2. **Casos de clientes depois.** Busque benchmarks da mesma taxonomia — por domínio, indústria,
   maturidade e tags (os blueprints seguem o schema golden-standard, com frontmatter:
   `caso_de_uso`, `cliente`, `industria`, `maturidade`, `tags`, `dominio`). Escolha **1–3 casos**
   relevantes e leia **somente esses**.
3. Se a busca do domínio não retornar nada na BU, diga isso com franqueza ao consultor e trate
   o processo como genuinamente novo (sem inventar um "padrão" que não existe).

## Padrões de integração (iPaaS), quando houver integração no escopo

Quando o pedido envolver iPaaS (ver `ipaas.md`), some uma busca pontual **antes** de desenhar o
flow do zero: procure no brain um padrão de integração já resolvido para o mesmo app/piece ou
tipo de evento (ex.: "Slack", "notificação por e-mail via iPaaS", "lookup em base externa"). Se
encontrar 1–2 casos relevantes, leia só esses e use como referência de trigger, steps e
mapeamentos — nunca reaproveite `externalId` de conexão de outro contexto.

**Se a busca não retornar nada, siga em frente sem alarde.** Diferente da base da BU, esse
acervo de padrões de integração é novo e pode ainda não cobrir o app/piece em questão — ausência
de resultado não é falha do brain nem do processo, é só um domínio ainda não documentado. Trate
como "genuinamente novo" (mesma régua da regra 3 acima) e siga direto para a descoberta normal
pelo catálogo iPaaS descrita em `ipaas.md`, sem bloquear, sem levar isso ao consultor como
pendência, e sem inventar um padrão que não existe.

## Regras

- **A BU é o esqueleto; os casos são variações.** Não invente estrutura sem base no
  conhecimento. O que for genuinamente novo, rotule como novo no spec.
- Registre no `spec.md` (`blueprints_utilizados`) os identificadores/títulos exatos dos
  documentos consultados no brain.
- O grounding acontece **antes** de perguntar (ver playbook do Planner): consultar o
  conhecimento primeiro faz as perguntas certas surgirem e evita perguntar o que a BU já responde.
- **Padrão de integração é apoio, não obrigação.** Ausência dele no brain nunca impede a
  integração aprovada de ser construída pelo catálogo iPaaS — o acervo ainda está crescendo.
