# Validação da versão 0.6.0

Verificação em 23/10/2026, horário de Brasília. Escopo: configuração externa,
fluxos carrossel/pesquisa/vídeo e preservação do runtime Motion. A sincronização
editorial completa de slides-canva e motion-designer não faz parte desta versão.

## Executado

- 16 testes Python de configuração e fallback: proposta sem criar pastas, ausência
  e corrupção de configuração, backup sem perda de mídia, template persistente,
  pesquisa sem sobrescrever, precedência do projeto, recusa de caminhos de cache,
  troca de versão, instaladores com configuração intacta e bloqueio ao iniciar Codex.
- 42 regressões dos scripts de carrossel, usando fixtures: estado, copy, prompts e
  índice. O revisor real foi simulado; não houve chamada a outro modelo.
- 32 testes dos scripts de vídeo e o script de regressões de corte de silêncio.
- 21 verificações do contrato de pesquisa e proveniência.
- 5 testes Node do runtime Motion: ausência de configuração, resolução externa e
  substituição da versão do plugin, recusa de caminho interno e de link simbólico
  de volta ao plugin, recusa de instalação interna antes de chamar npm.
- JSON/YAML, nomes de skills, links locais, sintaxe Python/Node e diff sem erros.
- Três contextos independentes avaliaram seis cenários cada: ambiente vazio,
  prévia com campos, modelo sem campos e revisor bloqueado, notícia sem causa de
  morte confirmada, atualização com configuração legada, e edição manual final.
  Foram 18 trajetórias simuladas aprovadas, não 18 integrações executadas.
- Revisão independente identificou e conferiu as correções de inicialização do
  revisor e de runtime/instaladores externos. Os casos novos falharam antes da
  correção e passaram depois; não foram apresentados como falhas de agente.

## Reproduzir os testes incluídos

Use Python 3.10+, Node 22+ e as dependências de edição para os testes de vídeo:

```sh
python3 -m unittest discover -s tests -v
node --test tests/test_motion_runtime.mjs
python3 skills/search/tests/test_contrato.py
python3 -m unittest discover -s skills/video-maker/scripts -p 'test_*.py' -v
python3 skills/video-maker/scripts/test_ar_morto.py
```

As 42 regressões de carrossel são da bateria local da fonte e foram executadas
contra uma cópia dos scripts distribuídos; essa bateria não faz parte do pacote.

## Limites

Não houve pesquisa real Sider/Exa nem gravação real no Canva. A rota de criação
por preenchimento depende de campos compatíveis e do acesso do usuário. Quando
não for suportada, a edição da cópia exige a aprovação de salvamento do conector;
a skill declara essa limitação e não inventa um link de conteúdo salvo.

Não foram instalados nem renderizados HyperFrames ou modelos de transcrição nesta
verificação. O engine continua HyperFrames 0.7.56; o que mudou foi seu destino e
sua resolução. Windows/Linux não foram executados nesta publicação. Os testes
com dublês verificam o encadeamento, sem provar o comportamento de serviços ou
programas ausentes. O profissional continua responsável pelas decisões clínicas.
