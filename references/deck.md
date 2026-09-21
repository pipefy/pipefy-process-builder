# Playbook — Porta E: deck para o cliente

Transforma o `diagnostico.md` (e, quando existir, o `roi.md`) num deck em PDF com identidade Pipefy.
Duas etapas: **redação**, por um **subagente de contexto limpo** (modelo default) que só vê os
arquivos da pasta e o template; **geração e QA**, pelo orquestrador (converte para PDF, roda o
checklist, oferece o upload ao Drive). Somente leitura no Pipefy.

Leia antes: `handoff-schemas.md` (seção 10), `deck-template.html`.

## Regra de ouro
**Todo número, nome de fase, campo, automação ou achado do deck existe em `diagnostico.md` ou
`roi.md`.** Nada vem da memória do modelo ou da conversa. O QA do orquestrador confere isso por
busca textual.

## Etapa 1 — Redação (subagente) → `deck.html` + `deck.md`
Prompt do orquestrador contém apenas: "leia e siga à risca `<caminho absoluto de references/deck.md>`,
Etapa 1", "somente leitura; use apenas o conteúdo dos arquivos da pasta", caminho absoluto da pasta
de trabalho e caminho absoluto de `references/`.

1. Leia `diagnostico.md` (e `roi.md`, se existir). Não leia o pipe.
2. Monte o roteiro **a partir do template** (`deck-template.html`), na ordem: capa → contexto (objetivo
   do processo, escopo do diagnóstico, data) → visão geral (3 a 6 KPIs: fases, campos, automações,
   agentes, flows, defeitos por severidade — só os que existem no arquivo) → achados (top 5–8 por
   severidade, com "onde" e impacto para o usuário; linguagem do cliente, sem jargão de API) →
   recomendações (as do diagnóstico; cada uma com a variação de `decision_catalog.md` citada quando
   houver, e as de IA marcadas com a classe `ai`) → roadmap (3 ondas: corrigir agora / evoluir /
   medir) → **ROI só se
   `roi.md` existir**, com o `modo` no título e os alertas no rodapé do slide; se `status:
   nao_calculavel`, o slide diz o que falta em vez de números → próximos passos.
3. Preencha os placeholders `{{...}}` do template; remova o slide de ROI quando não houver `roi.md`;
   ajuste a numeração do rodapé. `{{RECOMENDACOES_NOTA}}` cita a fonte das recomendações (ex.:
   "recomendações baseadas no padrão de referência e no catálogo de boas práticas da Pipefy
   Professional Services") — deixe em branco se nenhuma recomendação vier do catálogo. Rótulos com
   `[` `]` (ex.: nomes de fase `[SC] Scoping`) vão entre `<code>` — colchetes já quebraram diagrama
   em material real.
4. Sem segredo, token, e-mail pessoal ou dado de terceiro. Sem nome de SC.
5. Escreva `deck.html` e `deck.md` (seção 10 de `handoff-schemas.md`), com o Roteiro apontando a fonte
   de cada slide e os números usados. Devolva ao orquestrador: nº de slides, se há slide de ROI, e o
   que ficou em Pendências.

## Etapa 2 — Geração e QA (orquestrador)
1. **PDF** a partir do `deck.html` (o PDF se gera **sempre do arquivo final**, nunca de um artifact ou
   versão anterior — já se entregou PDF sem as atualizações):
   - Windows (Edge): `& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf="<pasta>\deck.pdf" "file:///<pasta>/deck.html"`
   - macOS (Chrome): `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf="<pasta>/deck.pdf" "file:///<pasta>/deck.html"`
   No Windows o Edge pode devolver o prompt **antes** de terminar de gravar o PDF: aguarde alguns
   segundos (ou o fim do processo `msedge`) antes do QA; arquivo ausente ou muito pequeno logo
   após o comando é sinal de corrida, não de template quebrado — reexecute a checagem.
   Sem Python nem Node necessários. Se nenhum dos dois existir, entregue o `deck.html` e registre.
2. **QA** (registrar em `deck.md`, seção QA):
   - camada de texto: `pdftotext deck.pdf -` (vem com o Git no Windows) devolve texto legível — PDF
     "impresso" de tela não serve;
   - todo número do deck existe em `diagnostico.md`/`roi.md` (busca textual, número a número);
   - nenhum `[`/`]` fora de `<code>`; nenhum placeholder `{{` sobrando;
   - nenhum segredo/dado pessoal; modo do ROI no título.
3. **Drive (opcional)**: se o conector do Google Drive estiver na sessão e o consultor pedir, suba o
   `deck.pdf` e registre o link em `drive_link`. **Compartilhar** com terceiros é ação externa — só com
   aprovação explícita registrada.
4. Entrega no chat: caminho do PDF, nº de slides, o que o consultor deve revisar antes de apresentar
   (Pendências), e se o kit de marca é provisório.

## Guardrails
- Não é relatório de auditoria técnica: severidades e impactos, sim; ids e nomes de mutation, não.
- Nenhum número sem fonte. Nenhum "cerca de". Se o diagnóstico não tem o dado, o slide não tem o dado.
- Tokens de marca em `deck-template.html` são **provisórios** até o kit oficial; não os altere por
  gosto — ajuste só quando o kit chegar, num único lugar (`:root`).
