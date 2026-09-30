# Operação segura no Canva

## Fonte de verdade

O Canva persistido é a fonte de verdade. Respostas da ferramenta sobre operações de rascunho não provam que o documento final foi salvo.

## Modelos conhecidos

Consulte `modelos-e-contexto.md` para identificar os papéis dos designs fornecidos pelo usuário. Confirme o alvo atual antes de editar.

## Fluxo de cópia

Quando o usuário pedir uma nova apresentação:

1. preserve o modelo original;
2. crie ou trabalhe em uma cópia;
3. depois que o tópico estiver definido, sugira o nome da cópia com base nele;
4. não altere a apresentação principal dos módulos, salvo pedido explícito de integração.

## Mapeamento dos campos

Inicie uma transação de edição e leia todos os `richtexts` e `pages`.

Mapeie por página:

- campo superior de título ou subtítulo;
- campo central de corpo;
- campo inferior de referências.

Não dependa apenas do texto do placeholder. Use também página, posição e conteúdo atual. Em slides de abertura, identifique o único título central.

Se os campos não forem editáveis ou estiverem incorporados a uma imagem, pare e explique a limitação.

## Aprovação única

O fluxo editorial fornece o gate antes da mutação. Quando o usuário aprovar o conteúdo e disser para criar ou preencher, essa autorização cobre:

1. aplicar o texto apresentado;
2. visualizar o rascunho;
3. executar o commit;
4. verificar o resultado salvo.

Não peça uma segunda aprovação apenas para gravar o mesmo conteúdo. Se o rascunho revelar que é necessária uma mudança material no texto aprovado, interrompa e peça nova autorização.

## Aplicação

- Agrupe as substituições em lote quando possível.
- Use `replace_text` para campos completos.
- Use `find_and_replace_text` somente quando a alteração for parcial e inequívoca.
- Não formate, redimensione, reposicione ou exclua elementos sem autorização.
- Mostre todas as prévias exigidas pelo conector, mas não transforme isso em um segundo gate quando já houve aprovação do lote.

## Commit e verificação obrigatória

Depois das operações:

1. confirme que cada resultado está como `success`;
2. execute o commit;
3. confirme o retorno `committed`;
4. abra uma nova leitura do mesmo design;
5. confira todas as páginas alteradas e os três campos esperados;
6. procure placeholders como `Subtítulo`, `Texto.Texto.Texto.Texto.Texto.` e `Referência.`;
7. confirme que os títulos esperados estão presentes;
8. encerre a sessão usada somente para auditoria sem modificar o documento.

Se a verificação mostrar conteúdo ausente, não declare sucesso. Refaça a transação usando os IDs atuais e verifique novamente.

## Entrega

Informe de forma objetiva:

- quantos slides foram preenchidos;
- se o commit foi confirmado;
- se a leitura posterior encontrou todos os campos e nenhum placeholder;
- o link direto para o Canva;
- a limitação do negrito parcial nas referências, se ainda relevante.

Quando o usuário pedir, abra o link final no Google Chrome e mantenha a aba disponível para revisão.
