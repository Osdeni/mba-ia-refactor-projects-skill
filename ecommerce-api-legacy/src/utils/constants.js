'use strict';

module.exports = Object.freeze({
    PAYMENT_STATUS: Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' }),
    // Regra do gateway fake: cartões iniciados por "4" são aprovados.
    CARD_APPROVED_PREFIX: '4',
    MESSAGES: Object.freeze({
        BAD_REQUEST: 'Bad Request',
        COURSE_NOT_FOUND: 'Curso não encontrado',
        PAYMENT_DENIED: 'Pagamento recusado',
        USER_NOT_FOUND: 'Usuário não encontrado',
        USER_DELETED: 'Usuário deletado',
        CHECKOUT_OK: 'Sucesso',
        NOT_FOUND: 'Not Found',
        INTERNAL_ERROR: 'Erro interno',
        ADMIN_DISABLED: 'Rotas administrativas desabilitadas (ADMIN_TOKEN não configurado)',
        ADMIN_INVALID_TOKEN: 'Token administrativo inválido',
    }),
    ADMIN_TOKEN_HEADER: 'X-Admin-Token',
});
