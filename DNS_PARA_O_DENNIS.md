# Configuração do domínio vitrinecaixa.com.br

Oi Dennis! Só falta um passo para o site entrar no ar em **vitrinecaixa.com.br**.

É mais simples do que o combinado antes: em vez de cadastrar vários registros, você só
troca os servidores DNS por dois. Leva uns 3 minutos.

---

## Passo a passo (registro.br)

**1.** Entrar em [registro.br](https://registro.br) com a conta do domínio.

**2.** Ir em **Meus Domínios** → clicar em `vitrinecaixa.com.br`.

**3.** Procurar a seção **Servidores DNS** (ou "DNS" → "Alterar servidores DNS").
Hoje ela está com os servidores automáticos do registro.br
(`a.auto.dns.br` e `b.auto.dns.br`).

**4.** Trocar para a opção de **DNS externo / usar outros servidores** e informar estes dois:

```
brett.ns.cloudflare.com
karsyn.ns.cloudflare.com
```

**5.** Remover os servidores antigos, se ainda aparecerem na lista.

**6.** Salvar.

---

## Observações

- Só esses dois. Não precisa de mais nenhum registro — o resto já está configurado do
  nosso lado.
- Os registros de proteção de e-mail que já existem no domínio (SPF, DMARC e o MX nulo)
  **foram preservados**, então nada muda em relação a e-mail.
- A propagação costuma levar de 30 minutos a algumas horas.

## Depois

Você recebe um e-mail do Cloudflare confirmando a ativação. Me avisa que eu finalizo
(certificado HTTPS e publicação) e te mando o link funcionando.

Hospedagem, certificado SSL e CDN são gratuitos — o único custo continua sendo a
anuidade do domínio no registro.br.
