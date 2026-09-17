'use strict';

const { timingSafeEqual } = require('crypto');
const config = require('../config');
const { ForbiddenError, UnauthorizedError } = require('../errors/AppError');
const { MESSAGES, ADMIN_TOKEN_HEADER } = require('../utils/constants');

function tokensMatch(provided, expected) {
    const a = Buffer.from(String(provided || ''));
    const b = Buffer.from(String(expected));
    return a.length === b.length && timingSafeEqual(a, b);
}

module.exports = (req, res, next) => {
    if (!config.adminToken) return next(new ForbiddenError(MESSAGES.ADMIN_DISABLED));
    if (!tokensMatch(req.get(ADMIN_TOKEN_HEADER), config.adminToken)) {
        return next(new UnauthorizedError(MESSAGES.ADMIN_INVALID_TOKEN));
    }
    return next();
};
