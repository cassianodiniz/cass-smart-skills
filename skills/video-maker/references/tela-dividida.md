# Tela dividida: escolher trechos e escrever o plano

O `montar.py` já sabe as medidas da casa:
- quadro de 1080×1920 a 30 fps, com 960 px em cima e 960 embaixo;
- degradê escuro de 90 px na emenda, nunca linha dura;
- fala vertical recortada "de peito" (`crop=1080:960:0:170` num vídeo de 1080×1920). Esse padrão supõe o rosto no alto do quadro. Antes de montar, olhe um quadro da fala: se a testa estiver abaixo de y≈500, use `corte_fala` com Y que deixe testa e queixo dentro do painel (no IMG_0533, sentado mais baixo, foi `1080:960:0:640`);
- só o áudio da fala, com fade de 0,1 s no fim.

O formato do plano está no topo do script. Aqui fica como decidir o que vai nele.

## Achar os pontos na fala

- Use os tempos de `fala.json` (campo `s` de cada palavra). A cena começa no `s` da palavra-âncora.
- O fim do reel fica entre o fim da última palavra e o início da seguinte. Exemplo: "displicente" termina em 37,02 e o "né?" seguinte começa em 37,10, então o fim é 37,08. Confira se o vídeo original não tem slide ou corte logo depois.
- Recorte a fala com `fala_inicio` e `fim` no plano. O vídeo original nunca é cortado.

## Escolher o trecho de cada tela

- Faça uma folha de contato por tela: `python scripts/folha.py "<tela>" folha_tela1.png`. Com 1 quadro por segundo dá pra ver a tela inteira; para detalhe, use `0 10 4` (10 s a 4 quadros por segundo).
- Prefira o momento em que a ação acontece, como o copo enchendo ou o rapaz comendo, e não a preparação.
- Cada cena dura de 2 a 5 s e troca a cada ideia nova da fala. Uma cena só por mais de 6 s cansa.
- Se uma tela mistura antes e depois, ela vira duas cenas, cada uma com o seu trecho e o seu recorte.

## Recorte da tela (o campo `corte`)

- **Tela vertical 1080×1920:** use `1080:960:0:Y`. Escolha Y olhando a folha, para o assunto inteiro caber, cabeça incluída. Exemplos:
  - "depois" segurando a calça: Y=760;
  - suco no copo: Y=820, para fugir de uma faixa preta no pé.
- **Tela 576×1024 (TikTok):** use `576:512:0:Y`. O script amplia para 1080×960. A tela 3 cortava a cabeça no meio e por isso subiu para Y=40.
- **Sem `corte`:** o script recorta pelo centro. `foco_y` (0 = topo, 1 = pé) e `foco_x` movem o recorte.
- **Largura cheia sempre.** Mostrar a tela inteira sobre fundo desfocado foi recusado.

## Fechar as contas

- As durações das cenas precisam somar o tempo de tela dividida, que é `fim` menos os trechos de `tela_cheia`. Se não somarem, o script recusa e diz a diferença.
- Ajuste a última cena antes de mexer nas âncoras.
- Motion feito na `motion-designer`: a duração dele é o intervalo exato entre a âncora em que ele entra e a próxima. Peça nessa duração, para não ter que cortar a animação.

## Tela cheia e efeitos

- Use `tela_cheia` para o fechamento e para trechos sem ilustração boa. Ali a legenda fica em y=960.
- `efeitos` aplica zoom (`1.2` a `1.35`) e preto e branco (`pb`) na fala. Vale na metade de baixo e na tela cheia. `foco_y_fala` diz a altura do rosto, para o zoom não cortar a cabeça.
- Zoom que anda: `"zoom": [1.30, 1.48], "centro": [x, y]` (pixels da fala, no rosto). Sai liso. Zoom com tranco ele recusa: se não ficar liso, não use.
- Motion em tela cheia por cima dele: em `sobreposicoes`, com `de` e `ate`. Só por pouco tempo.

## Final dos vídeos de IA

Quando o usuário pede CTA de seguir, use somente `perfil_instagram` configurado; sem ele, peça o @ ou omita o CTA:
- o final é só ele em `tela_cheia`, com zoom que anda (1,30 → 1,48) e o rosto no centro da tela;
- a pílula `python3 scripts/texto_png.py segue "<perfil_instagram>" <trabalho>/segue.mov` (com o clique e o balão de novo seguidor) entra em `sobreposicoes` acima da cabeça, a partir do "segue", com `y` = 134 (pílula em 380). Com o zoom do final a cabeça sobe: olhe um quadro do fim e, se a pílula cair no cabelo, suba o `y` até ela ficar acima (no IMG_0533 foi `y` = 30);
- sem celular, sem perfil desenhado e sem foto dele (foi recusado como "muito comercial").

## Ilustração de terceiros

Tela baixada de outro perfil é conteúdo de terceiro. No reel pessoal ele já usou assim. Num anúncio pago, avise antes de usar.
