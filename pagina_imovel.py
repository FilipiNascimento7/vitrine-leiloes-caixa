# -*- coding: utf-8 -*-
"""Gera a página de detalhe de um imóvel — tudo o que a Caixa mostra,
mais galeria de fotos e download do edital e da matrícula."""

import html
import os

CSS = """
:root{--azul:#0B4F9E;--azul-esc:#083A75;--laranja:#F39200;--verde:#1B8A4B;
 --tinta:#16202B;--cinza:#6B7785;--linha:#E3E8EE;--fundo:#F5F7FA;
 --sombra:0 1px 3px rgba(16,32,48,.08),0 8px 24px rgba(16,32,48,.06);}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Segoe UI",system-ui,-apple-system,Roboto,Arial,sans-serif;background:var(--fundo);
 color:var(--tinta);line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:var(--azul)}
header{background:linear-gradient(135deg,var(--azul),var(--azul-esc));color:#fff;padding:18px 24px}
.wrap{max-width:1180px;margin:0 auto}
.voltar{display:inline-block;color:#fff;text-decoration:none;font-size:13.5px;opacity:.9;margin-bottom:10px}
.voltar:hover{opacity:1}
header h1{font-size:23px;font-weight:700;letter-spacing:-.3px}
header .end{font-size:14px;opacity:.9;margin-top:4px}
.tags{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.tag{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.22);
 font-size:11.5px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;padding:4px 10px;border-radius:20px}
.tag.off{background:var(--verde);border-color:var(--verde)}

main{max-width:1180px;margin:0 auto;padding:22px 24px 60px;display:grid;
 grid-template-columns:1.55fr 1fr;gap:22px;align-items:start}
.card{background:#fff;border-radius:12px;box-shadow:var(--sombra);padding:20px 22px;margin-bottom:20px}
.card h2{font-size:13px;text-transform:uppercase;letter-spacing:.8px;color:var(--cinza);
 padding-bottom:10px;margin-bottom:14px;border-bottom:1px solid var(--linha)}

.precos{display:flex;gap:26px;align-items:baseline;flex-wrap:wrap}
.preco b{display:block;font-size:30px;font-weight:800;color:var(--azul);letter-spacing:-.8px}
.preco span,.aval span{font-size:11.5px;text-transform:uppercase;letter-spacing:.6px;color:var(--cinza)}
.aval b{display:block;font-size:18px;color:var(--cinza);text-decoration:line-through;font-weight:600}
.eco{margin-left:auto;text-align:right}
.eco b{display:block;font-size:18px;color:var(--verde);font-weight:800}

dl{display:grid;grid-template-columns:auto 1fr;gap:9px 18px;font-size:14px}
dt{color:var(--cinza)}
dd{font-weight:600;word-break:break-word}

.blocos p{font-size:14px;margin-bottom:8px}
.blocos ul{list-style:none;font-size:14px}
.blocos li{padding-left:16px;position:relative;margin-bottom:7px}
.blocos li:before{content:"•";position:absolute;left:0;color:var(--laranja);font-weight:700}
.blocos h3{font-size:12px;text-transform:uppercase;letter-spacing:.7px;color:var(--laranja);
 margin:16px 0 8px}
.blocos h3:first-child{margin-top:0}

.galeria{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}
.galeria img{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:8px;cursor:zoom-in;
 background:#E8ECF1;transition:transform .15s}
.galeria img:hover{transform:scale(1.02)}
.principal{width:100%;aspect-ratio:16/10;object-fit:cover;border-radius:12px;background:#E8ECF1;
 margin-bottom:12px;cursor:zoom-in}
.semfoto{width:100%;aspect-ratio:16/10;border-radius:12px;display:flex;align-items:center;
 justify-content:center;color:#A6B0BC;font-size:14px;
 background:repeating-linear-gradient(45deg,#EDF0F4,#EDF0F4 10px,#E8ECF1 10px,#E8ECF1 20px)}

.btn{display:block;text-align:center;text-decoration:none;font-size:14px;font-weight:700;
 padding:12px;border-radius:9px;margin-bottom:9px}
.btn.laranja{background:var(--laranja);color:#fff}
.btn.laranja:hover{background:#DB8300}
.btn.linha{border:1.5px solid var(--linha);color:var(--tinta);background:#fff}
.btn.linha:hover{border-color:var(--azul);color:var(--azul)}
.nota{font-size:12px;color:var(--cinza);margin-top:10px;line-height:1.5}

#lupa{position:fixed;inset:0;background:rgba(10,18,28,.92);display:none;align-items:center;
 justify-content:center;z-index:99;cursor:zoom-out;padding:30px}
#lupa img{max-width:100%;max-height:100%;border-radius:8px}
footer{text-align:center;padding:26px;color:var(--cinza);font-size:12px;border-top:1px solid var(--linha)}
@media(max-width:900px){main{grid-template-columns:1fr}}
"""


def _brl(v):
    if v is None:
        return "—"
    return "R$ " + f"{v:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _e(t):
    return html.escape(str(t or ""))


def gerar(im: dict, atualizado: str) -> str:
    d = im.get("detalhe") or {}
    campos = d.get("campos", {})
    areas = d.get("areas", {})
    blocos = d.get("blocos", {})
    fotos = d.get("fotos") or ([im["foto"]] if im.get("foto") else [])
    desconto = im.get("desconto") or 0

    titulo = f"{im['tipo']} em {im['bairro'] or im['cidade']}"
    endereco = d.get("endereco_completo") or im["endereco"]

    tags = [f'<span class="tag">{_e(im["modalidade"])}</span>',
            f'<span class="tag">{_e(im["tipo"])}</span>']
    if desconto > 0:
        tags.insert(0, f'<span class="tag off">{desconto:.1f}% de desconto</span>'.replace(".", ","))

    # fotos
    if fotos:
        principal = f'<img class="principal" src="{_e(fotos[0])}" alt="Foto do imóvel" onclick="ampliar(this.src)">'
        miniaturas = "".join(
            f'<img src="{_e(f)}" alt="Foto {i+1} do imóvel" loading="lazy" onclick="ampliar(this.src)">'
            for i, f in enumerate(fotos[1:], 0)
        )
        galeria = f'<div class="galeria">{miniaturas}</div>' if miniaturas else ""
    else:
        principal = '<div class="semfoto">sem foto cadastrada pela Caixa</div>'
        galeria = ""

    # ficha técnica: todos os campos que a Caixa exibe, na ordem em que aparecem
    ordem = ["Tipo de imóvel", "Número do imóvel", "Matrícula(s)", "Comarca", "Ofício",
             "Inscrição imobiliária", "Averbação dos leilões negativos",
             "Edital", "Número do item", "Leiloeiro(a)", "Data da disputa"]
    itens = []
    for k in ordem:
        if campos.get(k):
            itens.append((k, campos[k]))
    for k, v in campos.items():          # qualquer campo novo que a Caixa passe a exibir
        if k not in ordem and k not in ("Valor de avaliação", "Valor mínimo de venda",
                                        "Descrição", "Endereço"):
            itens.append((k, v))
    for k, v in areas.items():
        itens.append((k, v))
    itens += [("Cidade", im["cidade"]), ("Bairro", im["bairro"] or "—")]
    ficha = "".join(f"<dt>{_e(k)}</dt><dd>{_e(v)}</dd>" for k, v in itens)

    # blocos de texto (descrição, formas de pagamento, regras de despesas)
    rotulos = {"descricao_completa": "Descrição",
               "formas_pagamento": "Formas de pagamento aceitas",
               "regras_despesas": "Regras para pagamento das despesas"}
    partes = []
    for chave, rotulo in rotulos.items():
        linhas = blocos.get(chave)
        if not linhas:
            continue
        if len(linhas) == 1:
            corpo = f"<p>{_e(linhas[0])}</p>"
        else:
            corpo = "<ul>" + "".join(f"<li>{_e(l)}</li>" for l in linhas) + "</ul>"
        partes.append(f"<h3>{rotulo}</h3>{corpo}")
    if not partes and im.get("descricao"):
        partes.append(f"<h3>Descrição</h3><p>{_e(im['descricao'])}</p>")
    texto_livre = "".join(partes)

    # downloads
    botoes = [f'<a class="btn laranja" href="{_e(im["link"])}" target="_blank" rel="noopener">Dar lance no site da Caixa</a>']
    if d.get("edital"):
        botoes.append(f'<a class="btn linha" href="{_e(d["edital"])}" target="_blank" rel="noopener">📄 Baixar edital e anexos</a>')
    if d.get("matricula"):
        botoes.append(f'<a class="btn linha" href="{_e(d["matricula"])}" target="_blank" rel="noopener">📄 Baixar matrícula do imóvel</a>')

    aval = (f'<div class="aval"><span>Avaliação Caixa</span><b>{_brl(im["avaliacao"])}</b></div>'
            if im.get("avaliacao") and desconto > 0 else "")
    eco = (f'<div class="eco"><span>Economia</span><b>{_brl(im["economia"])}</b></div>'
           if im.get("economia") and im["economia"] > 0 else "")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(titulo)} — {_e(im['cidade'])} | Imóvel {_e(im['numero'])} · Leilão Caixa</title>
<style>{CSS}</style>
</head>
<body>

<header>
  <div class="wrap">
    <a class="voltar" href="../index.html">← Voltar para a vitrine</a>
    <h1>{_e(titulo)}</h1>
    <div class="end">{_e(endereco)}</div>
    <div class="tags">{''.join(tags)}</div>
  </div>
</header>

<main>
  <div>
    <div class="card">
      <div class="precos">
        <div class="preco"><span>Valor mínimo de venda</span><b>{_brl(im['preco'])}</b></div>
        {aval}
        {eco}
      </div>
    </div>

    <div class="card">
      <h2>Ficha do imóvel</h2>
      <dl>{ficha}</dl>
    </div>

    <div class="card blocos">
      <h2>Informações da Caixa</h2>
      {texto_livre or "<p>Sem informações adicionais.</p>"}
    </div>
  </div>

  <div>
    <div class="card">
      <h2>Fotos</h2>
      {principal}
      {galeria}
    </div>

    <div class="card">
      <h2>Documentos e lance</h2>
      {''.join(botoes)}
      <p class="nota">O lance é dado exclusivamente no site oficial da Caixa.
      Leia o edital e a matrícula antes de ofertar — eles trazem as condições de
      ocupação, dívidas e regras de pagamento do imóvel.</p>
    </div>
  </div>
</main>

<div id="lupa" onclick="this.style.display='none'"><img id="lupa-img" alt=""></div>

<footer>
  Dados do portal de Venda de Imóveis da Caixa Econômica Federal · atualizado em {_e(atualizado)}.<br>
  Esta página é uma vitrine informativa; confira sempre o site oficial antes de qualquer proposta.
</footer>

<script>
function ampliar(src){{
  document.getElementById('lupa-img').src = src;
  document.getElementById('lupa').style.display = 'flex';
}}
document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') document.getElementById('lupa').style.display = 'none';
}});
</script>
</body>
</html>
"""


def gravar_todas(imoveis, atualizado, pasta):
    destino = os.path.join(pasta, "imovel")
    os.makedirs(destino, exist_ok=True)
    for antigo in os.listdir(destino):
        if antigo.endswith(".html"):
            os.remove(os.path.join(destino, antigo))
    n = 0
    for im in imoveis:
        if not im.get("pagina"):
            continue
        with open(os.path.join(destino, f"{im['numero']}.html"), "w", encoding="utf-8") as f:
            f.write(gerar(im, atualizado))
        n += 1
    print(f"  {n} páginas de detalhe geradas em {destino}")
