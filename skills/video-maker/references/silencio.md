# Cortar silêncio

`scripts/cortar_silencio.py` veio da `video-ads-machine`. A lógica dele fica em `ar_morto.py`, com os testes em `test_ar_morto.py`.

```
python3 scripts/cortar_silencio.py <fala> --json <fala.json> --saida <trabalho>/fala_sem_silencio.mp4
```

- **Sem `--saida`:** o script só mostra o plano de cortes. Use isso pra conferir antes, se a fala for longa.
- **Por padrão:** sobra uma pausa de 0,16 s (`--respiro`) e só vãos de 0,4 s ou mais são cortados (`--limiar-corte`). Pra ritmo mais solto, use `--respiro 0.25`.
- **Conferência:** o script transcreve o resultado e para com erro se sumiu palavra. Se isso acontecer, aumente `--respiro` ou deixe o `--piso-db` mais rígido (por exemplo `-36`) e rode de novo. Não use `--sem-gate` sem motivo escrito.
- **A transcrição do vídeo cortado** fica ao lado dele (`fala_sem_silencio.json`). Use esse arquivo daqui pra frente.
- **Se mudar `ar_morto.py`,** rode `python3 -m unittest test_ar_morto` dentro de `scripts/`. Cada teste é um bug real que já comeu palavra.
