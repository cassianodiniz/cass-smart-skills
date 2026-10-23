# Estrutura card a card

Leia depois da captura e da classificação de domínio, antes de pesquisar a fundo e antes de escrever.

## Por que existe

O Cassiano decide a arquitetura do post, não a frase. Uma tese confirmada em prosa não é o mesmo que um mapa de cards aprovado: a tese diz "sobre o quê"; o mapa diz "o que entra em cada card e para que serve". A skill só escreve depois do mapa.

## Entrada adaptativa

1. Resuma em até 5 linhas o que entendeu: tese provável, público, material disponível, decisão ainda aberta.
2. Se perfil editorial (saúde ou IA) e formato não estiverem inequívocos no material, pergunte os dois **numa pergunta só**, no começo. Se o material já responde, confirme no resumo e não pergunte.
3. Pergunte somente o que ainda estiver faltando e que mudaria o mapa. Não repita perguntas já respondidas nem imponha entrevista quando o material é suficiente.

## Mapa provisório

Um portão único: o mapa carrega o eixo no cabeçalho. Não existe aprovação separada de eixo.

**Cabeçalho (3 linhas):** tese, público, tensão.

**Tabela:**

| Card | O que entra | Para que serve | Status ou pendência |
|---|---|---|---|

- `Status ou pendência` só quando houver dado ainda incerto, decisão real ou lacuna que impeça o card. Em card sem pendência, deixe vazio.
- A skill **pode propor por conta própria** uma linha de hipótese ("fala pública dela em 2022, a verificar") quando percebe uma lacuna que o Cassiano não pediu. Hipótese aparece no mapa como hipótese e nunca entra na copy como fato sem passar pela pesquisa.
- Não escreva frases finais de copy nesta etapa. O mapa diz o que o card faz, não como ele fala.

Depois do mapa provisório, pesquise somente os fatos escolhidos para ele (rota do domínio em `perfil-editorial.md`). Se a pesquisa mudar a arquitetura, mostre o mapa final com a alteração destacada.

## Gate

Termine sempre com: "Nenhuma copy foi escrita. Você pode aprovar a estrutura, mover um dado, remover um card ou pedir outra organização."

Ao receber aprovação explícita:

1. salve o mapa exato em `posts/<slug>/estrutura.md`;
2. execute `registrar_estrutura` e depois `aprovar_estrutura` (`scripts/estado.py`);
3. persista o estado.

Não escreva a copy enquanto `estrutura_aprovada_hash != estrutura_hash`. Qualquer mudança no mapa gera hash novo e exige nova aprovação.

## Atalhos

- `auditar`: não usa este gate porque não escreve.
- `incrementar`: mostre somente os cards afetados se o restante não mudar.
- `cassiano_final`: preserve a versão enviada; não reconstrua mapa.
- `retomar` em post antigo sem `estrutura_hash`: a primeira parada é montar o mapa a partir da copy existente e pedir aprovação; só então nova versão da skill.
