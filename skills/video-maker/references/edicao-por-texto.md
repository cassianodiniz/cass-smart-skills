# Edição por texto

Ele tira trechos da fala apagando palavras num texto, sem linha do tempo.

1. **Gerar o texto:** `python3 scripts/editar_texto.py preparar fala.json <trabalho>/edicao.md`. O arquivo sai com um aviso curto no topo e a fala em parágrafos, sem tempo nenhum.
2. **Abrir no editor dele:** `open -e <trabalho>/edicao.md` abre no TextEdit. Diga a ele, em uma linha: apagar o que não quer, salvar com Cmd+S e escrever "pronto" aqui.
3. **Esperar o "pronto".** Não leia o arquivo antes disso, porque ele pode estar no meio da edição.
4. **Cortar:** `python3 scripts/editar_texto.py aplicar fala.json <trabalho>/edicao.md <fala> <trabalho>/fala_editada.mp4`.
   - O script compara as palavras que sobraram com as da transcrição, corta o resto e transcreve o resultado pra conferir.
   - Se a conferência reprovar, mostre o trecho que deu errado e corrija. Não entregue sem resolver.
   - A transcrição do vídeo editado fica em `fala_editada.json`. Use esse arquivo daqui pra frente, na legenda e no plano.

## O que dá e o que não dá

- Só dá pra apagar. Palavra que ele escrever ou trocar é ignorada, e o script avisa. Se ele quiser dizer outra coisa, precisa gravar de novo.
- Se ele apagar meia palavra, ela some inteira ou fica inteira, o que for mais parecido com o texto dele.
- Ele pode pedir silêncio cortado também. Rode depois da edição por texto, sobre o `fala_editada.mp4`.
