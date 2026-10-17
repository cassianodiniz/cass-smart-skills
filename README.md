# Cass Smart Skills

Plugin de skills distribuído pelo GitHub. Versão atual: 0.2.0.

| Skill | Uso |
|---|---|
| ask-me | Alinhar decisões por entrevista antes de executar. |
| search | Pesquisar com Exa, conferir fontes e guardar pesquisas localmente. |
| slides-canva | Preparar slides, editar no Canva e criar imagens a partir do material fornecido. |
| no-ai-slop | Editar textos preservando a voz do autor ou apontar padrões de escrita. |
| motion-designer | Criar motion graphics mudo que ilustra um trecho de fala (metade de cima de um reel ou tela cheia), com HyperFrames. |

## Instalação no Codex

Com uma versão do Codex que suporte plugins, registre o catálogo deste repositório e instale o pacote:

```sh
codex plugin marketplace add cassianodiniz/cass-smart-skills --ref main
codex plugin add cass-smart-skills@cass-smart-skills
```

Esses comandos são instruções para quem quiser instalar. A criação deste repositório não instala o plugin na conta do autor. O registro do catálogo segue a [documentação oficial de plugins](https://developers.openai.com/plugins/build/plugins).

Depois de instalar, invoque a skill pelo nome. Exemplos:

- “Use ask-me para alinhar este pedido comigo.”
- “Use search para pesquisar este tema e guardar as fontes.”
- “Use slides-canva com este texto e o modelo que estou fornecendo.”
- “Use no-ai-slop para editar este rascunho.”
- “Use motion-designer para ilustrar esta fala de 7 segundos.”

## Dependências

As skills são instruções e arquivos auxiliares. O pacote não instala nem hospeda serviços externos.

- ask-me e no-ai-slop precisam apenas de um agente capaz de ler skills.
- motion-designer requer Node.js 22 ou superior, FFmpeg com FFprobe e a dependência local HyperFrames (`npm install --omit=dev --no-audit --no-fund` na pasta da skill). A transcrição opcional usa Whisper MLX local. Prints de telas de app ou de IA são fornecidos pelo usuário.
- search requer acesso ao Exa e ferramentas de busca/leitura compatíveis. Configure a conexão `https://mcp.exa.ai/mcp` e autentique pelo fluxo disponível no seu cliente; a disponibilidade de nomes de ferramentas deve ser conferida ali. Os scripts locais requerem Python 3.10 ou superior. Delegação usa os agentes e modelos disponíveis no ambiente; sem agentes, o fluxo deve ser executado diretamente e a limitação informada.
- slides-canva requer um conector Canva para editar e salvar apresentações e uma ferramenta de geração de imagens para essa parte do trabalho. O usuário fornece modelos, material científico e referências visuais. Chrome é necessário apenas quando solicitado para abrir o resultado.
- A gravação de pesquisas requer uma instalação local gravável da skill. Ambientes sem arquivos locais ou com cache somente leitura não satisfazem esse requisito.

## Pesquisas locais

A search resolve o destino pelo local do próprio script, nunca pelo diretório de trabalho:

```text
skills/search/pesquisas/
  BIBLIOTECA.md
  INDICE-MESTRE.md
  tema-AAAA-MM-DD/
    estudo.md
    referencias/
      INDICE.md
      fonte.md
```

O agente atualiza os índices durante a pesquisa. Execuções com o mesmo tema e data recebem sufixos para preservar resultados anteriores. `pesquisas/` fica fora do Git e dos arquivos gerados por `git archive`. Se a instalação impedir a gravação, a skill informa o problema e não escolhe outro destino. Reinstalar ou limpar o cache do cliente pode remover resultados locais; preserve-os antes dessas operações.

## Motion graphics

A motion-designer cria um vídeo mudo que ilustra o que a pessoa está falando, sem repetir a frase na tela. O padrão é 1080×960, para a metade de cima de um reel em tela dividida; 1080×1920 quando a cena pede tela cheia.

Fluxo:

1. O usuário cola a fala com a duração, ou aponta um vídeo com início e fim (a transcrição local é opcional).
2. A skill cria a pasta do motion com `node scripts/novo.mjs <pasta> <segundos>`, escreve a animação em HTML + GSAP e confere quadros reduzidos ao tamanho de um celular.
3. Entrega o HTML para aprovação e só então renderiza o MP4 com `node scripts/render.mjs <pasta>`, que verifica tamanho, duração, ausência de áudio e final parado.

O que vem no pacote:

- `references/estilo.md`: a receita de desenho (a coisa real no centro, câmera que passeia, enquadramentos de até 2,5 s, destaque que entra na palavra falada, anotação a pelo menos 24 px das letras, tela cheia de conteúdo) e dois exemplos aprovados em `references/estilo/`.
- `assets/fisiologia/`: seis esquemas de anatomia para temas de saúde, como referência de composição, sem validação clínica.
- Base HTML, GSAP, fontes e um mapa do Brasil por estado.

O que não vem: capturas de telas de aplicativos ou de IA. Quando a cena mostra uma tela, a estrutura segue o print que o próprio usuário fornece; sem print daquele app naquele aparelho, a skill pede um em vez de desenhar de memória. Motion acima de 15 s começa por uma cena-piloto para aprovação.

## Atualizações

A publicação de novas versões é manual, somente quando solicitada ao mantenedor. Não há automação de sincronização com as skills pessoais. As versões publicadas neste repositório são adaptadas para uso por outras pessoas.

## Créditos

Pacote organizado por Cassiano Diniz. A skill no-ai-slop mantém o copyright de Peter Yang e sua [licença MIT](skills/no-ai-slop/LICENSE). A biblioteca padrão Python basta para os scripts de pesquisa. Nenhuma licença global adicional foi atribuída ao restante do pacote.

## Validação

```sh
python3 skills/search/tests/test_contrato.py
python3 -m unittest discover -s tests -v
```

A validação cobre o contrato de fontes e o arquivamento local. Ela não cobre a motion-designer, que depende de Node, FFmpeg e HyperFrames instalados, nem prova execução real de uma pesquisa Exa, edição Canva ou geração de imagens; esses fluxos dependem dos serviços configurados no cliente.
