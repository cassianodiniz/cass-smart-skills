#!/usr/bin/env python3
"""Teste de contrato da skill `search` — roda sem dependência nenhuma.

    python3 tests/test_contrato.py

Por que existe
--------------
Item 10 do checklist da auditoria: *"existe ao menos um teste que roda e falha
quando alguma das nove regras acima for violada?"* Até 30/07/2026 a resposta era
não — a skill tinha 12 arquivos, todos de prosa, e nada impedia que uma edição
futura apagasse uma regra sem ninguém perceber (evidência E14).

O que ele NÃO faz, e é importante não confundir
-----------------------------------------------
Não julga a qualidade de uma pesquisa, não confere se uma afirmação é verdadeira,
e não substitui rodar a skill. Ele verifica que **as regras continuam escritas na
skill** — que o contrato não regrediu. É teste de texto, não de comportamento:
pega a regressão silenciosa (alguém "limpa" o SKILL.md e leva um campo junto),
não pega o modelo desobedecendo.

Cada caso aponta a evidência da auditoria que ele protege.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SKILL = RAIZ / "SKILL.md"
SEARCHING = RAIZ / "references" / "searching.md"
EXTRACTION = RAIZ / "references" / "extraction.md"

falhas: list[str] = []
passou = 0


def checa(nome: str, condicao: bool, porque: str) -> None:
    global passou
    if condicao:
        passou += 1
        print(f"  ok   {nome}")
    else:
        falhas.append(f"{nome} — {porque}")
        print(f"  FALHOU  {nome}")


def main() -> int:
    skill = SKILL.read_text(encoding="utf-8")
    searching = SEARCHING.read_text(encoding="utf-8")
    extraction = EXTRACTION.read_text(encoding="utf-8")
    tudo = skill + searching + extraction

    print("\nContrato da skill search\n" + "-" * 60)

    # --- 1. abrir a página é obrigatório para número (E1) ---
    checa(
        "1. abrir a página é obrigatório para todo número",
        "requires opening the page" in skill and "if the finding carries a number, open the page" in searching.lower(),
        "a regra sumiu; sem ela volta o E1 — extrair do snippet e nunca abrir a fonte",
    )

    # --- 2. o registro de proveniência tem todos os campos (E2, E5) ---
    campos = ["notes", "claim", "evidence_quote", "support_status", "sources",
              "credited_origin", "published", "measured_model", "measured_task",
              "measured_n", "measured_window", "independent_sources", "url"]
    faltando = [c for c in campos if f"`{c}`" not in skill]
    checa(
        "2. os campos do registro estão no template de despacho",
        not faltando,
        f"faltam: {', '.join(faltando)} — cada campo ausente é informação que some no caminho (E2, E5)",
    )

    # --- 2b. mais de uma fonte por afirmação, e contagem por origem (item 2 do checklist) ---
    checa(
        "2b. `sources` é lista e `independent_sources` conta origens, não links",
        "`sources` is a **list**" in skill and "count of origins, not of links" in skill,
        "voltou uma fonte só por afirmação; três ecos do mesmo original voltam a parecer três confirmações",
    )

    # --- 3. o mesmo registro está no extraction (os dois arquivos não podem divergir) ---
    faltando_ex = [c for c in campos if f'"{c}"' not in extraction and f"`{c}`" not in extraction]
    faltando_ex = [c for c in faltando_ex if c != "url"]  # aparece como chave dentro de sources[]
    checa(
        "3. extraction.md descreve o mesmo registro que o SKILL.md",
        not faltando_ex,
        f"faltam no extraction: {', '.join(faltando_ex)} — dois arquivos discordando deixam o subagente escolher",
    )

    # --- 4. measured_on colapsado NÃO pode voltar (furo pego pelo GPT em 30/07) ---
    checa(
        "4. o campo colapsado `measured_on` não voltou",
        "measured_on" not in tudo,
        "voltou o campo único; sem tarefa/N/janela separados a inversão de sinal do juiz passa de novo",
    )

    # --- 5. `not stated` é obrigatório, não opcional ---
    checa(
        "5. `not stated` é obrigatório e o campo nunca é omitido",
        "Never omit a field" in skill and "not stated" in skill,
        "sem isso o campo vazio volta a sumir em vez de aparecer — o buraco vira invisível",
    )

    # --- 6. as duas contagens, separadas (E6 / C1) ---
    checa(
        "6. results_requested e pages_opened existem e são separados",
        "results_requested" in skill and "pages_opened" in skill and "not the same number" in skill,
        "a métrica inflada voltou; foi ela que produziu o '220 fontes' (E6)",
    )
    checa(
        "7. o contador antigo `sources_reviewed` não voltou",
        "sources_reviewed" not in tudo,
        "voltou a soma de numResults apresentada como fontes revisadas (E6)",
    )

    # --- 8. concordância entre subagentes não é sinal de qualidade (E9) ---
    checa(
        "8. sobreposição entre subagentes não é vendida como 'good sign'",
        "overlap heavily (good sign)" not in skill and "saturated" in skill,
        "voltou a ler concordância de clones como confirmação (E9)",
    )

    # --- 9. destino de gravação é a biblioteca, não pasta relativa (E12) ---
    checa(
        "9. o destino é pesquisas/ dentro da skill, não ./exa-results/",
        "exa-results" not in tudo and "pesquisas/" in skill,
        "voltou a gravar em pasta relativa ao diretório de trabalho (E12)",
    )
    checa(
        "10. a skill chama o script de destino em vez de montar o caminho",
        "destino_pesquisa.py" in skill,
        "voltou a instrução em prosa com placeholder, sem garantia de que a pasta existe",
    )

    # --- 11. dedução separada de leitura ---
    checa(
        "11. Patterns/Notes são declarados como inferência, não como achado",
        "my inference across the sources above" in skill,
        "a dedução do modelo volta a chegar com a mesma cara das afirmações com fonte",
    )

    # --- 12. quem arquiva está escrito (furo da rodada fim-a-fim de 30/07) ---
    checa(
        "12. está escrito quem monta o arquivo da biblioteca",
        "Who writes what" in skill,
        "sem dono declarado, ninguém arquiva e a pesquisa não é reencontrável",
    )

    # --- 13. o subagente não roda no modelo mais fraco ---
    checa(
        "13. os subagentes não voltaram para o modelo mais fraco",
        'model: "haiku"' not in skill and 'enough capacity' in skill,
        "modelo perto do limite larga os campos estruturados e segue produzindo texto fluente",
    )

    # --- 14. gatilho de fetch é único (contradição introduzida e corrigida em 30/07) ---
    gatilhos = len(re.findall(r"open the page (?:when|only when|if the date)", tudo, re.I))
    checa(
        "14. não há gatilho de fetch condicional competindo com a regra geral",
        gatilhos == 0,
        "voltaram dois gatilhos diferentes; snippet com data e número satisfaz os dois sem abrir nada",
    )

    # --- 14b. a conferência do relato do subagente existe (item 7 / E10) ---
    checa(
        "14b. a skill manda conferir o relato do subagente antes de confiar",
        "conferir_registros.py" in skill and "the only witness" in skill,
        "voltou a compilar o relato do subagente sem nenhuma conferência (E10, classe D1)",
    )
    checa(
        "14c. a conferência semântica usa lentes diferentes, não repetição",
        "Three lenses beat three repetitions" in skill,
        "repetir a mesma pergunta re-confirma o mesmo ponto cego em vez de testá-lo",
    )
    conf = RAIZ / "scripts" / "conferir_registros.py"
    checa("14d. o script de conferência existe", conf.is_file(), "o conferente sumiu")
    if conf.is_file():
        import json, tempfile, os
        ruim = [{"claim": "erra em 5% dos casos", "support_status": "supports",
                 "independent_sources": 1, "sources": []}]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(ruim, fh); tmp = fh.name
        r = subprocess.run([sys.executable, str(conf), tmp], capture_output=True, text=True, timeout=30)
        os.unlink(tmp)
        checa(
            "14e. o conferente reprova um registro sem fonte",
            r.returncode == 1 and "nenhuma fonte" in r.stdout,
            f"saiu {r.returncode} sem apontar o problema — o conferente parou de conferir",
        )

    script = RAIZ / "scripts" / "destino_pesquisa.py"
    checa("15. o script de destino existe", script.is_file(), "o protetor do caminho sumiu")
    if script.is_file():
        r = subprocess.run([sys.executable, str(script), "--conferir"], capture_output=True, text=True, timeout=30)
        checa("16. confere sem criar a pasta", r.returncode == 0 and "pesquisas:" in r.stdout,
              f"saiu {r.returncode}: {r.stderr}")

    print("-" * 60)
    if falhas:
        print(f"\nREPROVADO — {len(falhas)} de {passou + len(falhas)} casos falharam:\n")
        for f in falhas:
            print(f"  • {f}")
        print("\nCada um desses corresponde a uma evidência da auditoria voltando a acontecer.")
        return 1
    print(f"\nOK — {passou} casos, contrato íntegro.")
    return 0


def test_contrato() -> None:
    """Ponte pro pytest. O porteiro do repo roda a suite com pytest e, sem isto,
    sai com 'no tests ran' (exit 5) e reporta falha sem ter conferido nada —
    alarme falso que ensina a ignorar o porteiro."""
    assert main() == 0


if __name__ == "__main__":
    raise SystemExit(main())
