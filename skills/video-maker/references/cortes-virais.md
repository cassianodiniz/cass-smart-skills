# Cortes de aula longa

Use `pastas.aulas` e `pastas.transcricoes` da configuração do usuário. Se ele pedir
um corte já escolhido, procure `cortes.json` e `cortes.md` no trabalho ou peça a
seleção, sem consultar bancos pessoais do autor. Salve os cortes escolhidos com
campos `n`, `aula`, `inicio`, `fim`, `gancho` e `literal` no trabalho.

## 1. Transcrição, uma vez só

- **Procure primeiro** em `<pastas.transcricoes>/<nome do arquivo sem extensão>.json`. Se existir, use.
- **Se não existir,** transcreva direto para lá: `python3 scripts/transcrever.py "<aula>" "<pastas.transcricoes>/<nome>.json"`. Junto sai o `.md` com tempos, que é o que você lê para escolher os trechos.
- **Com várias partes da mesma aula,** transcreva todas antes de sugerir, para a lista cobrir a aula inteira.
- **Se o transcritor avisar** que um trecho "continua só com 'É...'", abra o `.md` nesses minutos antes de sugerir cortes: ou é intervalo, ou é fala perdida que precisa de outra tentativa.

## 2. Sugerir trechos

Leia o `.md` inteiro e sugira de 3 a 6 trechos, ou o trecho que ele pedir. Cada trecho:
- tem de 30 a 90 s;
- tem uma ideia completa, com começo, meio e fim;
- prende nos 3 primeiros segundos: uma frase forte, uma pergunta ou uma contradição;
- termina numa conclusão, nunca no meio da ideia.

Os que mais rendem são os contraintuitivos, os polêmicos, os que derrubam um mito, os que contam um caso de paciente e os que dão uma regra prática.

Mostre numa tabela:

| # | Parte e tempo | Título | Primeira frase | Por que prende | Efeito sugerido |
|---|---|---|---|---|---|

- **Efeito sugerido:** zoom (1,2 a 1,35) e/ou preto e branco na frase de impacto (a contraditória, a polêmica). Só sugira; aplique depois do ok dele.
- **Tempos:** o início começa um pouco antes da primeira palavra, e o fim fica entre a última palavra e a seguinte.

## 3. Montar cada corte

- **Formato padrão:** tela dividida, ele embaixo e uma ilustração em cima. Para a metade de cima, pergunte se ele manda vídeos ou link, ou se você pede motion à `motion-designer`, e sugira o que ilustrar em cada frase.
- **Plano:**
  - `fala` é a aula, `fala_inicio` é o começo do trecho e `fim` é a duração do corte;
  - em aula horizontal, defina `foco_x` olhando uma folha de contato, para o rosto dele ficar no centro;
  - os efeitos aprovados vão em `efeitos`, no relógio do corte.
- **Legenda:** `gerar_legenda.py` com `--inicio <fala_inicio>` e `--fim <fala_inicio + fim>`. Veja [legenda.md](legenda.md).
- **Montar e conferir:** igual ao reel. Veja [tela-dividida.md](tela-dividida.md) e a conferência no SKILL.md.

## 4. Salvar

Depois da aprovação, copie cada corte para `pastas.saida`, preservando a versão
anterior. Plano, grupos e conferências ficam no trabalho. Nunca use Fotos ou
banco Notion do autor.
