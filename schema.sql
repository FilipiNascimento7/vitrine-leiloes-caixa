-- Banco de leads da vitrine (Cloudflare D1)
-- Rodar uma vez ao criar o banco.

CREATE TABLE IF NOT EXISTS leads (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  criado_em      TEXT NOT NULL,          -- ISO 8601, horário de Brasília
  nome           TEXT NOT NULL,
  telefone       TEXT NOT NULL,
  email          TEXT,
  mensagem       TEXT,
  imovel_numero  TEXT,
  imovel_titulo  TEXT,
  imovel_cidade  TEXT,
  imovel_preco   TEXT,
  imovel_url     TEXT,
  origem         TEXT,                   -- ex.: "ficha-imovel"
  ip             TEXT,
  user_agent     TEXT
);

CREATE INDEX IF NOT EXISTS idx_leads_criado ON leads (criado_em);
CREATE INDEX IF NOT EXISTS idx_leads_imovel ON leads (imovel_numero);
