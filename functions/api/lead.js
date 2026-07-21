// Recebe um lead do formulário da ficha de imóvel.
// Grava no banco D1 (binding "DB") e, se configurado, envia e-mail (Resend).
//
// Variáveis de ambiente (opcionais, configuradas no painel do Cloudflare Pages):
//   RESEND_API_KEY  -> chave do Resend para enviar o aviso por e-mail
//   LEAD_EMAIL      -> e-mail que recebe os leads
//   LEAD_FROM       -> remetente verificado no Resend (ex.: "Vitrine <leads@vitrinecaixa.com.br>")
// Sem essas variáveis, o lead é apenas gravado no banco (o painel mostra tudo).

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

function json(dados, status = 200) {
  return new Response(JSON.stringify(dados), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...CORS },
  });
}

export function onRequestOptions() {
  return new Response(null, { headers: CORS });
}

export async function onRequestPost(context) {
  const { request, env } = context;

  // aceita JSON (fetch) ou formulário tradicional (fallback sem JS)
  let dados = {};
  const tipo = request.headers.get("content-type") || "";
  try {
    if (tipo.includes("application/json")) {
      dados = await request.json();
    } else {
      const fd = await request.formData();
      for (const [k, v] of fd.entries()) dados[k] = v;
    }
  } catch (_) {
    return json({ ok: false, erro: "Requisição inválida." }, 400);
  }

  const txt = (v) => (v == null ? "" : String(v)).trim().slice(0, 800);

  // honeypot anti-spam: campo escondido "website" preenchido = bot
  if (txt(dados.website)) return json({ ok: true });

  const nome = txt(dados.nome);
  const telefone = txt(dados.telefone);
  const email = txt(dados.email);
  const mensagem = txt(dados.mensagem);

  if (nome.length < 2 || telefone.replace(/\D/g, "").length < 8) {
    return json({ ok: false, erro: "Informe nome e um telefone válido." }, 400);
  }

  const agora = new Date().toLocaleString("sv-SE", {
    timeZone: "America/Sao_Paulo",
  }); // "2026-07-21 15:40:12"

  const registro = {
    criado_em: agora,
    nome,
    telefone,
    email,
    mensagem,
    imovel_numero: txt(dados.imovel_numero),
    imovel_titulo: txt(dados.imovel_titulo),
    imovel_cidade: txt(dados.imovel_cidade),
    imovel_preco: txt(dados.imovel_preco),
    imovel_url: txt(dados.imovel_url),
    origem: txt(dados.origem) || "ficha-imovel",
    ip: request.headers.get("cf-connecting-ip") || "",
    user_agent: (request.headers.get("user-agent") || "").slice(0, 300),
  };

  // 1) grava no banco
  if (env.DB) {
    try {
      await env.DB.prepare(
        `INSERT INTO leads
           (criado_em, nome, telefone, email, mensagem,
            imovel_numero, imovel_titulo, imovel_cidade, imovel_preco, imovel_url,
            origem, ip, user_agent)
         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)`
      )
        .bind(
          registro.criado_em, registro.nome, registro.telefone, registro.email, registro.mensagem,
          registro.imovel_numero, registro.imovel_titulo, registro.imovel_cidade, registro.imovel_preco, registro.imovel_url,
          registro.origem, registro.ip, registro.user_agent
        )
        .run();
    } catch (e) {
      return json({ ok: false, erro: "Não consegui registrar agora. Tente pelo WhatsApp." }, 500);
    }
  }

  // 2) aviso por e-mail (só se configurado)
  if (env.RESEND_API_KEY && env.LEAD_EMAIL) {
    const html = `
      <h2>Novo interesse na vitrine</h2>
      <p><b>Nome:</b> ${registro.nome}<br>
      <b>Telefone:</b> ${registro.telefone}<br>
      <b>E-mail:</b> ${registro.email || "—"}</p>
      <p><b>Imóvel:</b> ${registro.imovel_titulo || "—"} (${registro.imovel_cidade || ""})<br>
      <b>Código:</b> ${registro.imovel_numero || "—"} · <b>Valor:</b> ${registro.imovel_preco || "—"}<br>
      <b>Ficha:</b> <a href="${registro.imovel_url}">${registro.imovel_url}</a></p>
      ${registro.mensagem ? `<p><b>Mensagem:</b> ${registro.mensagem}</p>` : ""}
      <p style="color:#888;font-size:12px">Recebido em ${registro.criado_em} (horário de Brasília)</p>`;
    try {
      await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.RESEND_API_KEY}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          from: env.LEAD_FROM || "Vitrine Caixa <onboarding@resend.dev>",
          to: [env.LEAD_EMAIL],
          reply_to: registro.email || undefined,
          subject: `Novo lead — ${registro.imovel_cidade || "imóvel"} (${registro.imovel_numero || "s/ código"})`,
          html,
        }),
      });
    } catch (_) {
      // não falha o lead se o e-mail cair; ele já está no banco
    }
  }

  return json({ ok: true });
}
