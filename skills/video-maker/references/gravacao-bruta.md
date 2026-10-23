# Gravação bruta: várias tentativas da mesma frase

Ele grava repetindo a frase até sair certa e deixa pausas longas entre as tentativas. O trabalho é ficar com uma tentativa de cada frase e juntar.

Cassiano também tem um formato de criação A/B de vídeos: em alguns casos ele pode querer alterar somente o gancho (primeiros segundos), fazendo o vídeo A com um gancho e um vídeo B com outro gancho. Cada um terá sua própria ilustração e headline.

## 1. Transcrição completa

O Whisper costuma inventar "E aí" nas pausas longas e pular a fala que vem depois. Depois de transcrever, procure trechos com som mas sem texto (pausa = mais de 1,5 s abaixo de -35 dB, com `silencedetect`) e transcreva cada um separado com `transcrever.py --inicio --fim`. Sem isso, frases inteiras somem do plano.

O JSON mantém `whisper_bruto`, avisos e as duas leituras quando refaz uma travada. Repetição reconhecida permanece no registro; texto igual não autoriza apagá-la como alucinação. A fala pode conter retomadas que o próprio Whisper omite: use o texto para localizar, não para aprovar o corte.

## 2. Escolher as tentativas

- **A última tentativa de cada frase é a certa.** Regra dele, de 10/10/2026. Não escolha a "mais limpa".
- No modo A/B o Cassiano falará durante o vídeo algo como "Gancho 1" ou "Gancho dois", nesse momento saiba que deve manter a versão final de cada gancho e criar 2 vídeos:
  - Gancho A + restante do vídeo. Gancho B + restante do vídeo (isso permite testar ganchos diferentes, com apenas a primeira imagem diferente).
- Começo abandonado sai ("A pior forma de você conversar com o Maia…").
- Se a tentativa recomeça no meio ("…ou que, com certeza, você já passou…"), fica a partir do recomeço.
- Antes de cortar, registre no trabalho uma seleção com **intervalo original da tentativa final, texto literal esperado, primeira/última palavra e intervalos abandonados que saem**. Cada recomeço exige uma decisão. Decimais do Whisper são estimativas; confira início/fim no áudio, sem usar a pausa como fronteira automática de tentativa.
- Exemplo: "um carrossel bem… [pausa] um carrossel bem escrito explica…" vira uma janela começando no **segundo** "um". Mandar as duas falas juntas para o cortador só retira a pausa e conserva a repetição. Se a localização continuar ambígua, sinalize a seleção como pendente e não a aprove pelo texto normalizado.
- Se uma tentativa anterior tem um gesto ou complemento curto que a última não tem (no IMG_0533, "é esse aqui" fazendo o L com a mão), ofereça emendar esse pedaço logo depois da última tentativa. Só entra com o sim dele.
- Mostre a lista antes de cortar: o que fica, o que sai e por quê.

## 3. Cortar

    python3 scripts/cortar_trechos.py <fala> <trabalho>/editado.mp4 '[[ini,fim], ...]' [--espelhar]

- Os tempos são do vídeo original. A folga de até 0,2 s antes/depois fica somente dentro da tentativa escolhida: não pode incluir palavra do começo abandonado ou da tentativa seguinte. A ordem da lista é a ordem do reel: um pedaço de antes pode vir depois de um de depois. O script apara por volume, com 0,03 s antes e até 0,12 s depois da voz, e retira pausas de 0,2 s ou mais; ele não escolhe tentativas. Exclusões entre janelas são preservadas, mesmo menores que 0,25 s. Para limites já ajustados, use `--solto`.
- Ele não se importa com a mudança de posição entre um trecho e outro: deixa o vídeo dinâmico. Não disfarce com zoom.
- **Fim do vídeo:** termina logo depois da última palavra, sem sobra.
- **Conferir:** o script transcreve o resultado. Ouça também o fim de cada trecho: palavra terminada em "s" pode perder o chiado. Compare frase a frase com a lista combinada. Se sobrar um pedaço de palavra na emenda ("Você já segue" no lugar de "Já segue"), ache a queda de volume entre as palavras e mova o corte uns centésimos.

### Conferencia da fala

O cortador gera `editado.cortes.json`, `editado.conferencia.json` e a pasta `editado_conferencia/` com um WAV por trecho, por emenda (±0,7 s) e do vídeo inteiro. Tudo começa **PENDENTE**. Preparação e transcrição bem-sucedidas significam rascunho renderizado, não fala aprovada.

1. Compare cada trecho com a seleção literal anterior ao corte. Preencha `esperado` com o texto escolhido; para cada item, ouça o recurso de áudio e registre `observado`, `resultado`, `metodo` e `evidencia.registro`. Nas emendas, confira a última e a primeira palavra e a ausência de retomada/sobra de sílaba. Depois confira a continuidade do vídeo integral.
2. Somente uma escuta realmente realizada pode usar `metodo: "escuta_direta"`, `resultado: "aprovado"` e `status: "DECLARACAO_COMPLETA"`. Whisper, inspeção de onda e imagens são apoio, não escuta. Sem capacidade de escuta na sessão, mantenha PENDENTE e entregue rascunho; não invente os registros para passar o verificador.
3. Rode `python3 scripts/conferencia_fala.py verificar <trabalho>/editado.conferencia.json`. Ausência de plano/arquivo, campo obrigatório vazio, item não conferido ou arquivo alterado reprova. O programa confere cobertura e identidade dos arquivos, **não comprova que alguém ouviu**.
4. Se encontrar falha, ajuste os limites, renderize em nova versão e repita a conferência. A declaração antiga não vale para outro MP4. Para preparar manualmente depois de uma montagem, use `python3 scripts/conferencia_fala.py preparar <video-final.mp4> <video.cortes.json>`: esse comando reinicia a declaração e só aceita plano cuja duração coincide. Montagem que muda tempos exige plano atualizado. Faça até duas rodadas de ajuste nesta entrega; se continuar ambíguo, mantenha os itens pendentes e reporte o trecho exato, sem aprovar.

| Sinal | Decisão |
|---|---|
| Transcrição parece limpa, mas há recomeço no original | Escolher a tentativa no original e conferir os limites; não aprovar pelo texto. |
| Imagens e duração passaram | Conferência visual feita; fala ainda depende da escuta registrada. |
| Não há ferramenta para ouvir nesta sessão | Preparar recursos e entregar rascunho identificado, sem declaração de escuta. |
| Uma exclusão curta reapareceu | Reprovar; preservar as janelas explícitas e conferir novamente as janelas no original. |

## 4. Encurtar, se ele pedir

Meta dele: menos de 40 s. Traga as sugestões numa tabela (frase, segundos ganhos, por que não faz falta) e corte só depois do ok. Saem primeiro:
- frase que repete a anterior ("E aí o resultado sai muito bom");
- mas só se a frase de antes terminar com a entonação descendo. Se ela fica "no ar" (ex.: "…tempo, neurônio e dinheiro" subindo), cortar a seguinte soa cortado. Nesse caso a frase fica;
- termo técnico que o público não entende ("sem gastar muito contexto da IA");
- rodeio antes do pedido final ("Antes de você receber a ferramenta,").

O que dá autoridade fica ("conhecido como o mago da programação"), mesmo encurtando.
