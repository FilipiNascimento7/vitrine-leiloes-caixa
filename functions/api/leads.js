// Lista os leads para o painel de consulta.
// Protegido por senha (variável de ambiente ADMIN_PASSWORD, configurada no Cloudflare).
// O painel envia a senha no cabeçalho "x-admin-key".

function json(dados, status = 200) {
  return new Response(JSON.stringify(dados), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

export async function onRequestGet(context) {
  const { request, env } = context;

  const senha = request.headers.get("x-admin-key") || "";
  if (!env.ADMIN_PASSWORD) {
    return json({ ok: false, erro: "Painel ainda não configurado (defina ADMIN_PASSWORD)." }, 503);
  }
  if (senha !== env.ADMIN_PASSWORD) {
    return json({ ok: false, erro: "Senha incorreta." }, 401);
  }
  if (!env.DB) {
    return json({ ok: false, erro: "Banco não conectado." }, 503);
  }

  try {
    const { results } = await env.DB.prepare(
      `SELECT id, criado_em, nome, telefone, email, mensagem,
              imovel_numero, imovel_titulo, imovel_cidade, imovel_preco, imovel_url, origem
         FROM leads
        ORDER BY id DESC
        LIMIT 1000`
    ).all();
    return json({ ok: true, total: results.length, leads: results });
  } catch (e) {
    return json({ ok: false, erro: "Falha ao ler os leads." }, 500);
  }
}
