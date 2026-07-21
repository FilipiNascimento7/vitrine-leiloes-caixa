# Configuração do domínio vitrinecaixa.com.br

Oi Dennis! O site da vitrine de imóveis de leilão já está pronto e no ar num endereço
provisório. Para ele passar a responder em **vitrinecaixa.com.br**, falta só apontar o
DNS no registro.br. São 5 registros e leva uns 5 minutos.

---

## Passo a passo

**1.** Entrar em [registro.br](https://registro.br) com a conta do domínio.

**2.** Ir em **Meus Domínios** → clicar em `vitrinecaixa.com.br`.

**3.** Abrir **Editar Zona DNS** (em alguns painéis aparece como "DNS" → "Editar zona").

**4.** Se já houver registros nos campos `@` ou `www`, **apagar** os antigos.

**5.** Criar estes 5 registros:

| Tipo | Nome / Host | Valor / Dados |
|------|-------------|---------------|
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |
| CNAME | `www` | `filipinascimento7.github.io.` |

**6.** Salvar.

---

## Observações

- Os **quatro IPs** são os servidores oficiais do GitHub Pages, que é onde o site está
  hospedado. Precisa cadastrar os quatro — é redundância, se um cair os outros respondem.
- No campo **Nome/Host**, alguns painéis pedem `@` e outros pedem deixar **em branco** —
  os dois significam "o domínio raiz". Se o registro.br não aceitar `@`, deixe vazio.
- No CNAME do `www`, se o painel exigir, mantenha o **ponto final** depois de `.io`
  (`filipinascimento7.github.io.`).
- A propagação costuma levar cerca de 1 hora, mas pode ir até 24h.

## Depois de propagar

Me avisa que eu concluo a configuração no GitHub (ativar o domínio e o certificado HTTPS).
Aí o site responde em:

- **https://vitrinecaixa.com.br** — endereço principal
- **https://www.vitrinecaixa.com.br** — redireciona para o principal

Hospedagem e certificado SSL são gratuitos (GitHub Pages) — não há custo mensal além da
anuidade do domínio no registro.br.
