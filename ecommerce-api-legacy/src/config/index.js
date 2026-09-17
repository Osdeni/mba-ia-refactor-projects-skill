'use strict';

/**
 * Configuração lida do ambiente com defaults seguros.
 * A aplicação precisa subir sem `.env` e sem variáveis exportadas.
 * Este módulo não importa nada da aplicação.
 */

const DEV_GATEWAY_KEY = 'pk_test_dev_only_change_me';

function parseBool(value, fallback) {
  if (value === undefined || value === '') return fallback;
  return /^(1|true|yes)$/i.test(String(value).trim());
}

function parsePort(value, fallback) {
  const port = Number(value);
  return Number.isInteger(port) && port > 0 && port < 65536 ? port : fallback;
}

/** Avisos sobre defaults inseguros; o composition root decide como registrá-los. */
function insecureDefaultWarnings() {
  const warnings = [];
  if (config.paymentGatewayKey === DEV_GATEWAY_KEY) {
    warnings.push('PAYMENT_GATEWAY_KEY não definida — usando chave de desenvolvimento');
  }
  if (!config.adminToken) {
    warnings.push('ADMIN_TOKEN não definido — rotas administrativas responderão 403');
  }
  return warnings;
}

const config = Object.freeze({
  env: process.env.NODE_ENV || 'development',
  debug: parseBool(process.env.DEBUG, false),
  // O app original escutava em todas as interfaces (app.listen(port)); mantido por compatibilidade.
  host: process.env.HOST || '0.0.0.0',
  port: parsePort(process.env.PORT, 3000),
  // ':memory:' reproduz o comportamento original (banco recriado e populado a cada boot).
  dbFile: process.env.DB_FILE || ':memory:',
  // null → rotas administrativas respondem 403 até que ADMIN_TOKEN seja definido.
  adminToken: process.env.ADMIN_TOKEN || null,
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || DEV_GATEWAY_KEY,
  smtpUser: process.env.SMTP_USER || '',
  logLevel: (process.env.LOG_LEVEL || 'info').toLowerCase(),
  jsonBodyLimit: process.env.JSON_BODY_LIMIT || '100kb',
  insecureDefaultWarnings,
});

module.exports = config;
