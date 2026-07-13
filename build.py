# -*- coding: utf-8 -*-
"""
Coletor de imóveis de leilão da Caixa — Curitiba e Região Metropolitana (RMC).

Baixa a lista pública da Caixa (CSV por estado), filtra por município e
modalidade de venda, e gera:
  - docs/dados.json          -> consumido pela vitrine online (GitHub Pages)
  - docs/vitrine_offline.html-> vitrine com os dados embutidos (abre por duplo clique)
  - docs/imoveis.xlsx        -> planilha para prospecção interna
  - docs/imoveis.csv         -> mesma base em CSV (UTF-8 com BOM, abre no Excel)

Rodar:  python build.py
"""

import csv
import io
import json
import os
import re
import sys
import unicodedata
from datetime import datetime, timezone, timedelta

import requests

# ----------------------------------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------------------------------

UF = "PR"
CSV_URL = f"https://venda-imoveis.caixa.gov.br/listaweb/Lista_imoveis_{UF}.csv"

# Curitiba + os 28 demais municípios da Região Metropolitana de Curitiba
MUNICIPIOS = [
    "Curitiba",
    "Adrianópolis",
    "Agudos do Sul",
    "Almirante Tamandaré",
    "Araucária",
    "Balsa Nova",
    "Bocaiúva do Sul",
    "Campina Grande do Sul",
    "Campo do Tenente",
    "Campo Largo",
    "Campo Magro",
    "Cerro Azul",
    "Colombo",
    "Contenda",
    "Doutor Ulysses",
    "Fazenda Rio Grande",
    "Itaperuçu",
    "Lapa",
    "Mandirituba",
    "Piên",
    "Pinhais",
    "Piraquara",
    "Quatro Barras",
    "Quitandinha",
    "Rio Branco do Sul",
    "Rio Negro",
    "São José dos Pinhais",
    "Tijucas do Sul",
    "Tunas do Paraná",
]

# Modalidades desejadas. O casamento é por "contém" sobre o texto normalizado,
# então "Venda Direta Online" e "Compra Direta" (nomes que a Caixa alterna) entram.
MODALIDADES_ALVO = [
    "licitacao aberta",
    "venda online",
    "venda direta",
    "compra direta",
]

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
FUSO_BR = timezone(timedelta(hours=-3))

# ----------------------------------------------------------------------------
# UTILITÁRIOS
# ----------------------------------------------------------------------------


def normalizar(texto: str) -> str:
    """minúsculas, sem acento, sem espaços duplicados."""
    if texto is None:
        return ""
    t = unicodedata.normalize("NFKD", str(texto))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip().lower()


MUNICIPIOS_NORM = {normalizar(m): m for m in MUNICIPIOS}


def para_float(valor: str):
    """'123.456,78' / 'R$ 1.200,00' -> 123456.78"""
    if valor is None:
        return None
    t = re.sub(r"[^\d,.\-]", "", str(valor))
    if not t:
        return None
    # formato brasileiro: ponto = milhar, vírgula = decimal
    t = t.replace(".", "").replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
PAGINA_BUSCA = "https://venda-imoveis.caixa.gov.br/sistema/busca-imovel.asp?sltTipoBusca=imoveis"


def _parece_bloqueio(texto: str) -> bool:
    t = normalizar(texto[:3000])
    return any(x in t for x in ("bot manager", "captcha", "<html", "<head"))


def _baixar_via_requests() -> str:
    resp = requests.get(CSV_URL, timeout=120, headers={"User-Agent": UA})
    resp.raise_for_status()
    return resp.content.decode("latin-1")


def _baixar_via_navegador() -> str:
    """A Caixa bloqueia IPs de datacenter com desafio JS (Radware Bot Manager).
    Um navegador real resolve o desafio; depois buscamos o CSV com os cookies dele."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        nav = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        ctx = nav.new_context(
            user_agent=UA,
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            viewport={"width": 1366, "height": 768},
        )
        ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
        )
        pg = ctx.new_page()
        pg.goto(PAGINA_BUSCA, wait_until="domcontentloaded", timeout=90_000)

        # dá tempo do desafio JS rodar e gravar os cookies
        for _ in range(6):
            pg.wait_for_timeout(3000)
            if not _parece_bloqueio(pg.content()[:2000]) or "busca" in pg.url:
                break

        # busca o CSV de dentro da própria página (mesma origem, cookies válidos)
        b64 = pg.evaluate(
            """async (url) => {
                const r = await fetch(url, {credentials: 'include'});
                const buf = new Uint8Array(await r.arrayBuffer());
                let s = '';
                for (const b of buf) s += String.fromCharCode(b);
                return btoa(s);
            }""",
            CSV_URL,
        )
        nav.close()

    import base64
    return base64.b64decode(b64).decode("latin-1")


def baixar_csv() -> str:
    print(f"Baixando {CSV_URL} ...")
    try:
        texto = _baixar_via_requests()
        if not _parece_bloqueio(texto):
            print(f"  ok — {len(texto)/1024:.0f} KB (requisição direta)")
            return texto
        print("  bloqueado por desafio anti-bot — tentando via navegador…")
    except Exception as e:
        print(f"  requisição direta falhou ({e}) — tentando via navegador…")

    texto = _baixar_via_navegador()
    if _parece_bloqueio(texto):
        raise RuntimeError(
            "A Caixa devolveu uma página de desafio anti-bot mesmo pelo navegador."
        )
    print(f"  ok — {len(texto)/1024:.0f} KB (via navegador)")
    return texto


def achar_cabecalho(linhas):
    """A Caixa põe algumas linhas de título antes do cabeçalho real."""
    for i, linha in enumerate(linhas[:15]):
        n = normalizar(linha)
        if "cidade" in n and "modalidade" in n:
            return i
    raise RuntimeError(
        "Não encontrei a linha de cabeçalho no CSV. "
        "O layout da Caixa pode ter mudado — primeiras linhas:\n"
        + "\n".join(linhas[:8])
    )


def achar_coluna(cabecalho, *palavras):
    """Retorna o índice da 1ª coluna cujo nome contém todas as palavras."""
    for i, nome in enumerate(cabecalho):
        n = normalizar(nome)
        if all(p in n for p in palavras):
            return i
    return None


# ----------------------------------------------------------------------------
# PIPELINE
# ----------------------------------------------------------------------------


def coletar():
    bruto = baixar_csv()
    linhas = [l for l in bruto.splitlines() if l.strip(";").strip()]
    idx_cab = achar_cabecalho(linhas)

    leitor = csv.reader(io.StringIO("\n".join(linhas[idx_cab:])), delimiter=";")
    cabecalho = next(leitor)
    cabecalho = [c.strip() for c in cabecalho]
    print("Colunas detectadas:", cabecalho)

    col = {
        "numero": achar_coluna(cabecalho, "imovel") or 0,
        "uf": achar_coluna(cabecalho, "uf"),
        "cidade": achar_coluna(cabecalho, "cidade"),
        "bairro": achar_coluna(cabecalho, "bairro"),
        "endereco": achar_coluna(cabecalho, "endereco"),
        "preco": achar_coluna(cabecalho, "preco"),
        "avaliacao": achar_coluna(cabecalho, "avaliacao"),
        "desconto": achar_coluna(cabecalho, "desconto"),
        "descricao": achar_coluna(cabecalho, "descricao"),
        "modalidade": achar_coluna(cabecalho, "modalidade"),
        "link": achar_coluna(cabecalho, "link"),
    }
    faltando = [k for k, v in col.items() if v is None and k != "uf"]
    if faltando:
        raise RuntimeError(f"Colunas não encontradas no CSV: {faltando}")

    def campo(linha, chave):
        i = col[chave]
        if i is None or i >= len(linha):
            return ""
        return linha[i].strip()

    imoveis = []
    modalidades_vistas = {}
    total_pr = 0

    for linha in leitor:
        if not linha or len(linha) < 5:
            continue
        total_pr += 1

        cidade_norm = normalizar(campo(linha, "cidade"))
        if cidade_norm not in MUNICIPIOS_NORM:
            continue

        modalidade = campo(linha, "modalidade")
        mod_norm = normalizar(modalidade)
        modalidades_vistas[modalidade] = modalidades_vistas.get(modalidade, 0) + 1
        if not any(alvo in mod_norm for alvo in MODALIDADES_ALVO):
            continue

        numero = campo(linha, "numero")
        preco = para_float(campo(linha, "preco"))
        avaliacao = para_float(campo(linha, "avaliacao"))
        desconto = para_float(campo(linha, "desconto"))

        # desconto real, recalculado (a coluna da Caixa às vezes vem vazia)
        if (desconto in (None, 0)) and preco and avaliacao and avaliacao > 0:
            desconto = round((1 - preco / avaliacao) * 100, 2)

        descricao = campo(linha, "descricao")
        link = campo(linha, "link")

        # id interno usado nas URLs da Caixa (hdnimovel) — serve para a foto
        m = re.search(r"hdnimovel=(\d+)", link)
        hdn = m.group(1) if m else re.sub(r"\D", "", numero)

        imoveis.append(
            {
                "numero": numero,
                "cidade": MUNICIPIOS_NORM[cidade_norm],
                "bairro": campo(linha, "bairro").title(),
                "endereco": campo(linha, "endereco"),
                "preco": preco,
                "avaliacao": avaliacao,
                "desconto": desconto,
                "economia": (round(avaliacao - preco, 2) if (preco and avaliacao) else None),
                "tipo": classificar_tipo(descricao),
                "area": extrair_area(descricao),
                "quartos": extrair_quartos(descricao),
                "aceita_financiamento": "financiamento" in normalizar(descricao)
                and "nao aceita financiamento" not in normalizar(descricao),
                "aceita_fgts": "fgts" in normalizar(descricao)
                and "nao aceita fgts" not in normalizar(descricao),
                "descricao": descricao,
                "modalidade": modalidade,
                "link": link,
                "foto": f"https://venda-imoveis.caixa.gov.br/fotos/F{hdn}21.jpg" if hdn else "",
            }
        )

    imoveis.sort(key=lambda i: (i["desconto"] or 0), reverse=True)
    return imoveis, total_pr, modalidades_vistas


def classificar_tipo(descricao: str) -> str:
    d = normalizar(descricao)
    for chave, rotulo in [
        ("apartamento", "Apartamento"),
        ("casa", "Casa"),
        ("sobrado", "Casa"),
        ("terreno", "Terreno"),
        ("lote", "Terreno"),
        ("gleba", "Terreno"),
        ("comercial", "Comercial"),
        ("loja", "Comercial"),
        ("sala", "Comercial"),
        ("galpao", "Comercial"),
        ("predio", "Comercial"),
        ("rural", "Rural"),
        ("chacara", "Rural"),
        ("fazenda", "Rural"),
    ]:
        if chave in d:
            return rotulo
    return "Outros"


def extrair_area(descricao: str):
    d = normalizar(descricao)
    m = re.search(r"([\d.,]+)\s*(?:m2|m²|de area privativa|de area total)", d)
    if m:
        return para_float(m.group(1))
    return None


def extrair_quartos(descricao: str):
    d = normalizar(descricao)
    m = re.search(r"(\d+)\s*(?:quarto|dormitorio|qto|dorm)", d)
    return int(m.group(1)) if m else None


# ----------------------------------------------------------------------------
# SAÍDAS
# ----------------------------------------------------------------------------


def gravar(imoveis, total_pr, modalidades_vistas):
    os.makedirs(SAIDA, exist_ok=True)
    agora = datetime.now(FUSO_BR)

    resumo = {
        "atualizado_em": agora.strftime("%d/%m/%Y às %H:%M"),
        "atualizado_iso": agora.isoformat(),
        "total": len(imoveis),
        "total_pr": total_pr,
        "municipios": sorted({i["cidade"] for i in imoveis}),
        "modalidades": sorted({i["modalidade"] for i in imoveis}),
        "valor_total": round(sum(i["preco"] or 0 for i in imoveis), 2),
        "desconto_medio": (
            round(sum(i["desconto"] or 0 for i in imoveis) / len(imoveis), 1) if imoveis else 0
        ),
    }

    # 1) JSON (vitrine online)
    with open(os.path.join(SAIDA, "dados.json"), "w", encoding="utf-8") as f:
        json.dump({"resumo": resumo, "imoveis": imoveis}, f, ensure_ascii=False, indent=1)

    # 2) CSV (Excel-friendly)
    campos = [
        "numero", "cidade", "bairro", "endereco", "tipo", "area", "quartos",
        "preco", "avaliacao", "desconto", "economia", "modalidade",
        "aceita_financiamento", "aceita_fgts", "link", "descricao",
    ]
    with open(os.path.join(SAIDA, "imoveis.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(imoveis)

    # 3) XLSX (prospecção interna) — opcional, só se openpyxl estiver instalado
    try:
        gravar_xlsx(imoveis, resumo, campos)
    except ImportError:
        print("  (openpyxl não instalado — pulei o .xlsx; o .csv foi gerado)")

    # 4) Vitrine offline com dados embutidos
    modelo_path = os.path.join(SAIDA, "index.html")
    if os.path.exists(modelo_path):
        with open(modelo_path, encoding="utf-8") as f:
            html = f.read()
        embutido = (
            "<script>window.DADOS_EMBUTIDOS = "
            + json.dumps({"resumo": resumo, "imoveis": imoveis}, ensure_ascii=False)
            + ";</script>"
        )
        html_off = html.replace("<!--DADOS-->", embutido)
        with open(os.path.join(SAIDA, "vitrine_offline.html"), "w", encoding="utf-8") as f:
            f.write(html_off)

    print("\n" + "=" * 62)
    print(f"  {resumo['total']} imóveis em Curitiba + RMC "
          f"(de {total_pr} no PR inteiro)")
    print(f"  Desconto médio: {resumo['desconto_medio']}%")
    print(f"  Atualizado em:  {resumo['atualizado_em']}")
    print("=" * 62)
    print("\n  Modalidades encontradas no PR (as marcadas com * entraram):")
    for mod, qtd in sorted(modalidades_vistas.items(), key=lambda x: -x[1]):
        marca = "*" if any(a in normalizar(mod) for a in MODALIDADES_ALVO) else " "
        print(f"   {marca} {mod or '(vazio)'}: {qtd}")
    print(f"\n  Arquivos gerados em: {SAIDA}\n")


def gravar_xlsx(imoveis, resumo, campos):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "Imóveis"

    titulos = {
        "numero": "Nº Imóvel", "cidade": "Cidade", "bairro": "Bairro",
        "endereco": "Endereço", "tipo": "Tipo", "area": "Área (m²)",
        "quartos": "Quartos", "preco": "Preço (R$)", "avaliacao": "Avaliação (R$)",
        "desconto": "Desconto (%)", "economia": "Economia (R$)",
        "modalidade": "Modalidade", "aceita_financiamento": "Financia?",
        "aceita_fgts": "FGTS?", "link": "Link Caixa", "descricao": "Descrição",
    }

    ws.append([titulos[c] for c in campos])
    cab_fill = PatternFill("solid", fgColor="1B4D8F")
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = cab_fill
        c.alignment = Alignment(horizontal="center", vertical="center")

    for im in imoveis:
        ws.append([im.get(c) for c in campos])

    for i, c in enumerate(campos, start=1):
        letra = get_column_letter(i)
        larguras = {"endereco": 42, "descricao": 60, "link": 30, "bairro": 20,
                    "cidade": 20, "modalidade": 20}
        ws.column_dimensions[letra].width = larguras.get(c, 14)
        if c in ("preco", "avaliacao", "economia"):
            for cel in ws[letra][1:]:
                cel.number_format = 'R$ #,##0.00'
        if c == "desconto":
            for cel in ws[letra][1:]:
                cel.number_format = '0.0"%"'

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    ws2 = wb.create_sheet("Resumo")
    ws2.append(["Atualizado em", resumo["atualizado_em"]])
    ws2.append(["Imóveis (Curitiba + RMC)", resumo["total"]])
    ws2.append(["Imóveis no PR inteiro", resumo["total_pr"]])
    ws2.append(["Desconto médio (%)", resumo["desconto_medio"]])
    ws2.append(["Valor total ofertado (R$)", resumo["valor_total"]])
    ws2.append([])
    ws2.append(["Modalidades incluídas"])
    for m in resumo["modalidades"]:
        ws2.append(["", m])
    ws2.column_dimensions["A"].width = 30
    ws2.column_dimensions["B"].width = 40
    for c in ("A1", "A2", "A3", "A4", "A5", "A7"):
        ws2[c].font = Font(bold=True)

    wb.save(os.path.join(SAIDA, "imoveis.xlsx"))


if __name__ == "__main__":
    try:
        imoveis, total_pr, mods = coletar()
    except Exception as e:
        print(f"\nERRO: {e}\n", file=sys.stderr)
        sys.exit(1)
    if not imoveis:
        print("\nAVISO: nenhum imóvel bateu com os filtros. "
              "Confira as modalidades listadas abaixo e ajuste MODALIDADES_ALVO.\n")
    gravar(imoveis, total_pr, mods)
