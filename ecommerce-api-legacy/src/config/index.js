'use strict';

/**
 * Configuração lida do ambiente com defaults seguros.
 * A aplicação precisa subir sem `.env` e sem variáveis exportadas.
 */
function envBool(name, fallback) {
    const raw = process.env[name];
    if (raw === undefined || raw === '') return fallback;
    return ['1', 'true', 'yes', 'on'].includes(String(raw).trim().toLowerCase());
}

function envInt(name, fallback) {
    const parsed = Number.parseInt(process.env[name], 10);
    return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

const DEV_GATEWAY_KEY = 'pk_test_dev_only_change_me';

const config = Object.freeze({
    env: process.env.NODE_ENV || 'development',
    debug: envBool('DEBUG', false),
    host: process.env.HOST || '0.0.0.0',
    port: envInt('PORT', 3000),
    dbFile: process.env.DB_FILE || ':memory:',
    adminToken: process.env.ADMIN_TOKEN || null,
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || DEV_GATEWAY_KEY,
    logLevel: process.env.LOG_LEVEL || 'info',
    usingDefaultGatewayKey: !process.env.PAYMENT_GATEWAY_KEY,
});

module.exports = config;
