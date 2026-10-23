# Canva

Leia somente quando a entrega pedida inclui Canva e a copy final já foi aprovada (por Cassiano ou Carine).

## Aprovação única antecipada

O pedido de entregar o post no Canva, combinado com a aprovação explícita da copy
e de seu hash, é a aprovação única antecipada do lote de edição. Registre esse
hash em `canva_lote_autorizado_hash` e, antes da primeira chamada ao Canva,
registre `Pronto` no banco configurado ou no registro local, conforme `notion.md`. Ele cobre copiar, preencher e
`commit_editing_transaction`; mostre as thumbnails exigidas pelo conector, mas
continue sem pedir outra confirmação.

Se a entrega no Canva não fazia parte do pedido, a aprovação textual sozinha não
autoriza criar design.

## Operação

1. Chame `get_design` com o ID conhecido do template original. ID inválido
   bloqueia a montagem e exige o link correto.
2. Chame `copy_design`, persista imediatamente `template_copia_id` e confira
   que ele difere de `canva_original_id`. Em card único, escolha a variante
   adequada e passe `page_numbers` com exatamente uma página.
3. Chame `start_editing_transaction` na cópia. Mostre a thumbnail retornada,
   guarde `transaction_id` e `pages`, e pare se não houver richtexts editáveis.
4. Mapeie cards para os elementos existentes. Quando houver várias imagens,
   confira os assets e thumbnails com `get_assets`.
5. Para foto local recebida no chat ou WhatsApp, chame
   `upload_asset_from_url` usando `asset_file`. Para URL HTTPS já pública,
   use `url`. Nunca publique arquivo privado num host temporário.
6. Aplique em lote `replace_text` e `update_fill` por
   `perform_editing_operations`. Não altere fonte, cor, tamanho, posição ou
   páginas. Em página responsiva, respeite o conjunto restrito de operações.
7. Mostre as thumbnails retornadas, valide ordem, cards vazios, overflow e
   ausência de conteúdo do post anterior.
8. Com o hash ainda igual a `canva_lote_autorizado_hash`, chame
   `commit_editing_transaction` diretamente, sem pedir outra confirmação.
9. Só depois do sucesso registre `canva_commit_em` e mostre o link da cópia.

Se a copy precisar mudar, chame `cancel_editing_transaction`, volte ao fluxo
textual, gere nova versão e passe novamente pelo revisor. Falha de commit significa
que nada foi salvo; não alegue sucesso.

Nunca edite o template original.
