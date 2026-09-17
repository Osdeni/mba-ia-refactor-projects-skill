'use strict';

const config = require('../config');
const logger = require('../utils/logger');
const { PAYMENT_STATUS, CARD_APPROVED_PREFIX } = require('../utils/constants');

if (config.usingDefaultGatewayKey) {
    logger.warn('PAYMENT_GATEWAY_KEY não definida — usando chave de desenvolvimento');
}

/**
 * Gateway fake: aprova cartões que começam com o prefixo configurado.
 * A chave do gateway fica em config e nunca é logada; o cartão é mascarado.
 */
function charge(cardNumber, amount) {
    logger.info(`Processando cartão ${logger.maskCard(cardNumber)} (valor ${amount})`);
    return String(cardNumber).startsWith(CARD_APPROVED_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
}

module.exports = { charge };
