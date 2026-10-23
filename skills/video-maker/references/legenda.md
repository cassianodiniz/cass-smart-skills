# Legenda dinâmica

O estilo já vem fixo no `scripts/gerar_legenda.py`:
- Inter ExtraBold 99 px, branca, com sombra escura e suave atrás (sem contorno);
- a palavra falada na cor de destaque: dourado `#EFA819` em vídeo de IA (padrão), verde `#19B85A` com `--nutricao`;
- pulo curto na entrada de cada grupo;
- posição y=1040 na tela dividida (alto da metade dele, logo abaixo da divisa) e y=960 na tela cheia.

Ele aprovou esse estilo em 10/10/2026. Não mude sem ele pedir.

## Headline (os 3,5 s iniciais)

Nos primeiros 3,5 s não tem legenda: entra uma headline-gancho, parecida com a fala (não precisa ser igual). É o único texto exatamente na divisa entre as telas.

```
python3 scripts/texto_png.py headline "<texto>" <trabalho>/headline.png --destaque "<palavras>" [--emoji 🤯] [--nutricao]
```

- O script já faz: caixa alta, mesma fonte da legenda, caixa preta, letra branca, destaque na cor do tipo de vídeo, sem ponto final. Uma linha só em 62 px quando couber na largura; se não couber, 2 linhas próximas e da mesma largura em 52 px. Ele aprovou a linha única em 12/10/2026.
- `--destaque` pinta palavra por palavra: `--destaque "GPT Lula"` pinta só essas duas.
- Emoji: um ou dois, que despertem curiosidade e combinem com o vídeo. Vão no fim; `--emoji-inicio` põe no começo.
- No plano, entra em `sobreposicoes` com `"de": 0, "ate": 3.5` e `"y"` = 960 menos metade da altura que o script imprime.

## Quando tem legenda

O padrão é sem legenda: só a headline, porque a metade de cima já ilustra a fala. Legenda só quando ele pedir. Nesse caso:
- siga os passos abaixo;
- comece depois da headline: apague do `.ass` as linhas que começam antes de 3,5 s.

## Passos

1. **Rascunho dos grupos:** `python3 scripts/gerar_legenda.py fala.json grupos.txt --rascunho --fim <fim>`. Fica um grupo por linha.
2. **Revise o rascunho à mão.** É a parte que exige julgamento:
   - Cada linha é um pedaço de ideia de 1 a 4 palavras, que se lê de uma vez. A quebra automática parte ideias ("aqui e | ela perdeu"); conserte.
   - Pergunta curta fica junto: "Milagre, né?", com a vírgula, porque "né" é pergunta.
   - As palavras precisam ser as da transcrição e na mesma ordem. Se o Whisper escreveu diferente do que ele falou (por exemplo "para o" onde ele disse "pro"), corrija no `fala.json` (veja abaixo). A legenda mostra o que ele falou, do jeito que falou.
3. **Gerar:** `python3 scripts/gerar_legenda.py fala.json grupos.txt --saida legenda.ass --fim <fim> --tela-cheia 27.9-37.08`.
   - Se aparecer o aviso de largura, parta a linha em duas.
   - Os tempos de `--tela-cheia` são os do reel.
4. **Montar:** coloque `"legenda": "legenda.ass"` no plano. O `montar.py` queima a legenda na mesma passada.

## Quando a transcrição errou

- **Palavra mal escrita pelo Whisper:** corrija o campo `w` dela no `fala.json`, sem mexer nos tempos, e gere de novo. Se duas palavras viram uma ("para o" → "pro"), deixe a primeira com o texto novo e o fim da segunda, e apague a segunda.
- **Frase estranha que pode ser o que ele falou mesmo:** não corrija sozinho. Pergunte a ele, citando o trecho. Exemplo: "três mil calorias por ml".

## Fala que começa no meio do vídeo (cortes de aula)

Passe `--inicio <s>` com o mesmo valor do `fala_inicio` do plano. A legenda sai no relógio do reel.
