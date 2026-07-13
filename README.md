# Vitrine de Imóveis de Leilão — Caixa | Curitiba e RMC

Vitrine online que lista **todos os imóveis da Caixa em Curitiba e nos 28 municípios da Região Metropolitana**, nas modalidades **Licitação Aberta, Venda Online e Venda Direta / Compra Direta** — atualizada automaticamente **todo dia às 7h**, na nuvem, **sem depender do seu computador estar ligado**.

Duas visões na mesma página:
- **Vitrine** — cards com foto, preço, % de desconto e botão "ver no site da Caixa". Para mandar pro cliente.
- **Tabela** — todos os campos, ordenável, com exportação para CSV/Excel. Para prospecção.

---

## Como colocar no ar (uma vez só, ~10 minutos)

### 1. Criar o repositório
1. Entre em [github.com](https://github.com) (crie uma conta gratuita se não tiver).
2. Clique em **New repository**.
3. Nome: `vitrine-leiloes-caixa` · visibilidade **Public** · **não** marque nada em "Initialize".
4. **Create repository**.

### 2. Subir os arquivos
Na tela do repositório recém-criado, clique em **uploading an existing file** e arraste **todo o conteúdo desta pasta**:

```
build.py
requirements.txt
README.md
.github/workflows/atualizar-vitrine.yml      <- importante, mantenha as pastas
docs/index.html
```

> Se o navegador não deixar arrastar as pastas `.github` e `docs`, instale o [GitHub Desktop](https://desktop.github.com) — ele sobe tudo de uma vez, preservando a estrutura.

### 3. Ligar as permissões e o Pages
- **Settings → Actions → General → Workflow permissions** → marque **Read and write permissions** → **Save**.
- **Settings → Pages → Source** → selecione **GitHub Actions**.

### 4. Rodar a primeira coleta
- Aba **Actions** → workflow **"Atualizar vitrine de imóveis Caixa"** → **Run workflow**.
- Em ~1 minuto o link fica disponível em **Settings → Pages**, no formato:

```
https://SEU-USUARIO.github.io/vitrine-leiloes-caixa/
```

Esse é o link que você compartilha. A partir daí ele se atualiza sozinho todo dia às 7h.

---

## Rodar na sua máquina (opcional)

Precisa de [Python](https://python.org/downloads) instalado (marque **"Add Python to PATH"** na instalação).

Dê duplo clique em **`atualizar-agora.bat`**. Ele baixa a lista da Caixa, gera os arquivos e abre a vitrine.

Saídas geradas em `docs/`:

| Arquivo | Para quê |
|---|---|
| `vitrine_offline.html` | Vitrine completa em um arquivo só — abre por duplo clique, funciona sem internet, pode mandar por e-mail |
| `imoveis.xlsx` | Planilha com filtros automáticos + aba de resumo |
| `imoveis.csv` | Mesma base, para importar em CRM |
| `dados.json` | Base que alimenta a vitrine online |

---

## Ajustes rápidos

Tudo fica no topo do **`build.py`**:

- **Trocar de estado ou cidade** → edite `UF` e a lista `MUNICIPIOS`.
- **Incluir outra modalidade** (ex.: *Leilão SFI*) → adicione `"leilao sfi"` em `MODALIDADES_ALVO`.
- **Mudar o horário da atualização** → em `.github/workflows/atualizar-vitrine.yml`, a linha `cron: "0 10 * * *"` está em UTC (10h UTC = 7h de Brasília).

Quando o script roda, ele **lista no final todas as modalidades encontradas no PR** e marca com `*` as que entraram — assim você vê na hora se a Caixa renomeou alguma.

---

## Fonte dos dados

Lista pública oficial da Caixa: `https://venda-imoveis.caixa.gov.br/listaweb/Lista_imoveis_PR.csv`

O `% de desconto` é recalculado (`1 - preço / avaliação`) quando a Caixa deixa a coluna em branco. As fotos vêm do padrão de URL do portal; imóveis sem foto cadastrada mostram um placeholder.

⚠️ Sempre confira edital, matrícula e condições de ocupação no site oficial da Caixa antes de qualquer proposta.
