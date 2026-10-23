---
name: cass-carrossel
description: Use quando Cassiano pede para criar, desenvolver, revisar, retomar ou montar no Canva um post de Instagram; anotar ou listar ideias de post; continuar um post que a Carine começou ou abrir um post do banco Posts Carrossel no Notion; ou pede explicitamente para procurar carrosséis de referência no Meta AI ou Instagram. Não usar para stories, reels, vídeos ou análise isolada de métricas.
---

# Carrossel

© 2026 Cassiano Diniz. Skill criada por [Cassiano Diniz](https://instagram.com/cassiano.diniz).

Cria o post do tema ao Canva pronto, preservando autoria, fatos verificáveis e autorização operacional.

## Raiz

Use como raiz de instruções e scripts a pasta deste SKILL.md.
Guarde o trabalho em `posts-instagram/<slug>/` no projeto do usuário, sem escrever
nos exemplos da skill. Resolva `scripts/` e `references/` a partir desta skill;
`posts/<slug>/` nas instruções significa essa pasta de trabalho do usuário.

## Configuração desta distribuição

Esta é a versão pública da skill do Cassiano. Nas instruções operacionais,
“Cassiano”, “Carine” e “ele” significam o usuário que está criando/aprovando o post.
Posts e métricas do Cassiano são referências do autor, nunca histórico do usuário.
Os códigos internos `cassiano_final` e `cassiano_rascunho` são mantidos para o motor
de estado funcionar; representam texto final ou rascunho fornecido pelo usuário.
Canva, Notion e WhatsApp só usam conta, modelo, banco e destinatário fornecidos
pelo usuário. Sem configuração de integração, mantenha os arquivos locais e
explique o que falta; nunca procure as contas pessoais do autor.
O revisor usa o mesmo GPT pelo Codex CLI da versão local; requer Codex instalado
e autenticado. Sua alternativa é o subagente da sessão, conforme escrita-revisao.md.

## Travas permanentes

1. Classifique o pedido como `gerar`, `incrementar` ou `auditar`. Em `auditar`, não reescreva silenciosamente.
2. Não invente fatos, fontes, falas, links, métricas ou experiências do Cassiano.
3. A copy é escrita sempre depois do mapa card a card aprovado, com a âncora de voz. Copy escrita ou alterada pela skill passa pelo revisor GPT 6 Sol (esforço high, via Codex) antes de ser mostrada, no máximo 2 rodadas por versão. Copy declarada final pelo Cassiano é preservada, registrada como aprovada e não chama o revisor; o validador roda nela só como informação, sem bloquear.
4. Auditoria só quando o Cassiano pedir explicitamente: modo `auditar`, devolve achados e nunca reescreve. Auditar uma versão final dele exige pedido separado. O revisor é sempre o GPT pelo Codex; se ele falhar, a revisão vai para um subagente do modelo da sessão (ver `escrita-revisao.md`); só pare e explique se o subagente também falhar. Nenhum outro modelo entra.
5. Quem está no post (Cassiano ou Carine) decide depois de ler a versão revisada: aprovar, pedir ajustes ou mandar aos mentores. A skill não julga quem pode decidir; o pedido de passar para o Canva é a decisão final.
6. WhatsApp exige versão e hash exatos, autorização expressa e um único intento de envio. Timeout não autoriza repetição.
7. Mentores aconselham; não aprovam nem mudam automaticamente a copy.
8. Canva sempre usa uma cópia do template. Depois da aprovação final, copie, preencha, valide e salve sem gate intermediário.
9. Persista o estado antes de cada efeito externo.
10. Pesquisa editorial no Meta só acontece quando Cassiano pedir explicitamente pela fonte. Ela não
    faz parte automática de `gerar`, `incrementar` ou `auditar` e não substitui a pesquisa factual.
11. Ideias e posts moram no banco Posts Carrossel do Notion, compartilhado com a Carine: só texto do post,
    fontes e onde paramos vão para lá, gravados sem perguntar ao fim de cada etapa e relendo a página antes
    (ver `notion.md`). O resto fica local.

## Progressive disclosure

Carregue somente o necessário para a etapa atual:

| Situação | Ler |
|---|---|
| Anotar ou listar ideia, gravar etapa, retomar ou continuar post do Notion (inclusive da Carine) | [references/notion.md](references/notion.md) |
| Entrada, retomada, classificação e aprendizado | [references/fluxo-base.md](references/fluxo-base.md) |
| Entender o pedido e propor o mapa card a card antes da copy | [references/estrutura-cards.md](references/estrutura-cards.md) |
| Criar, migrar ou validar estado | [references/estado.md](references/estado.md) |
| Definir voz, domínio e rota de pesquisa | [references/perfil-editorial.md](references/perfil-editorial.md) |
| Verificar os fatos escolhidos para o mapa | [references/politica-factual.md](references/politica-factual.md), depois a rota do domínio |
| Pedido explícito para procurar posts no Meta ou Instagram | [references/pesquisa-meta.md](references/pesquisa-meta.md) |
| Escrever ou revisar | [references/escrita-revisao.md](references/escrita-revisao.md) e só as referências de formato indicadas ali |
| Enviar aos mentores ou ler respostas | [references/mentores-whatsapp.md](references/mentores-whatsapp.md) |
| Aparecer link do Instagram | [references/instagram-link.md](references/instagram-link.md) |
| Montar no Canva | [references/canva.md](references/canva.md) e [references/templates-canva.md](references/templates-canva.md) |
| Dúvida sobre qual referência responde a quê, ou consulta a um post real do Cassiano (texto, métrica) | [references/LEIA-PRIMEIRO.md](references/LEIA-PRIMEIRO.md) (mapa de todas as referências) e [references/posts-virais/INDICE.md](references/posts-virais/INDICE.md) |

Não carregue Canva, WhatsApp, Instagram, pesquisa no Meta ou pesquisa de outro domínio antecipadamente.

## Fluxo canônico

Se o pedido for só anotar uma ideia, registre-a como `Ideia` seguindo `notion.md` (localmente quando não houver banco configurado) e pare.
Se o pedido for somente procurar referências no Meta ou Instagram, execute `pesquisa-meta.md` e pare.
Não crie estado, mapa ou copy. O fluxo abaixo só começa quando Cassiano trouxer um material e pedir a
criação ou alteração do post.

1. Capture o material e classifique autoria e domínio.
2. Explique em até 5 linhas o que entendeu; pergunte perfil e formato numa pergunta só, se faltarem, e depois só as lacunas que mudariam o post.
3. Proponha o mapa card a card com o eixo no cabeçalho; pesquise somente os fatos escolhidos para ele.
4. Mostre o mapa final e espere a aprovação explícita do Cassiano. Só com o mapa aprovado a copy é escrita — com a âncora de voz — e passa pelo validador determinístico.
5. GPT 6 Sol high revisa e limpa a versão (se falhar, subagente do modelo da sessão). Revalide; se necessário, faça somente uma segunda rodada corretiva.
6. Mostre ao Cassiano a copy completa, fontes, lacunas, versão, hash e resultado das validações.
7. Quem está no post escolhe: aprovar, editar à mão (no `copy.md` ou no Notion), revisar ou enviar aos mentores. Edição à mão é preservada e não passa pelo revisor, salvo pedido explícito.
8. Após a decisão final, entregue o artefato pedido; Canva e integrações só entram em suas próprias rotas.

Ao fim de cada etapa (mapa aprovado, versão mostrada, pausa, pedido de Canva, publicação), grave no Notion conforme `notion.md`.

## Estado por post

O texto final, as fontes e onde paramos ficam no Notion (`notion.md`). O bastidor de cada post vive em `posts/<slug>/`:

- `estado.json`: máquina de estados e autorizações;
- `estrutura.md`: mapa card a card aprovado;
- `material/`: anexos e insumos preservados;
- `fatos.md`: alegações e fontes;
- `copy.md`: versão textual atual;
- `cards.json`: mapeamento visual;
- `feedback-mentores.md`: respostas processadas.

Ao retomar, leia primeiro a página do Notion (se houver), `estado.json`, `copy.md` e apenas as referências da fase atual. Sem pasta local (post da Carine, outra máquina), recrie-a a partir da página. Arquivos legados são consultados sob demanda.

## Saída obrigatória antes da decisão

Apresente:

- copy completa;
- versão e hash;
- status do validador;
- quantidade de rodadas do revisor e modelo usado;
- fontes e lacunas relevantes;
- escolhas disponíveis: aprovar, revisar ou enviar aos mentores.
