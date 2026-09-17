'use strict';

module.exports = Object.freeze({
  PAYMENT_STATUS: Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' }),
  /** Regra do gateway simulado: cartões iniciados por este prefixo são aprovados. */
  CARD_APPROVED_PREFIX: '4',
  MESSAGES: Object.freeze({
    BAD_REQUEST: 'Bad Request',
    COURSE_NOT_FOUND: 'Curso não encontrado',
    PAYMENT_DENIED: 'Pagamento recusado',
    CHECKOUT_SUCCESS: 'Sucesso',
    USER_NOT_FOUND: 'Usuário não encontrado',
    USER_DELETED: 'Usuário deletado',
    NOT_FOUND: 'Not Found',
    INTERNAL_ERROR: 'Erro interno',
    ADMIN_DISABLED: 'Rotas administrativas desabilitadas (ADMIN_TOKEN não configurado)',
    ADMIN_INVALID_TOKEN: 'Token administrativo inválido',
  }),
});
