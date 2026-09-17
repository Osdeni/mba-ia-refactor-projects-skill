'use strict';

const config = require('../config');
const logger = require('../utils/logger');
const { PAYMENT_STATUS, CARD_APPROVED_PREFIX } = require('../utils/constants');

/**
 * Gateway de pagamento simulado (mesma regra do projeto original):
 * cartões iniciados por "4" são aprovados, os demais recusados.
 * A chave do gateway é lida da configuração e nunca vai para o log.
 */
function charge({ card, amount }) {
  const keyKind = config.paymentGatewayKey.startsWith('pk_live_') ? 'live' : 'test';
  logger.info(`Processando cartão ${logger.maskCard(card)} (chave ${keyKind}) — valor ${amount}`);
  return String(card).startsWith(CARD_APPROVED_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
}

module.exports = { charge };
