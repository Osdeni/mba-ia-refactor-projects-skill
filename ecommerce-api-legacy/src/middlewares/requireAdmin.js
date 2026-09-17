'use strict';

const { timingSafeEqual } = require('crypto');
const config = require('../config');
const { ForbiddenError, UnauthorizedError } = require('../errors/AppError');
const { MESSAGES } = require('../utils/constants');

function tokensMatch(provided, expected) {
  const a = Buffer.from(String(provided));
  const b = Buffer.from(String(expected));
  return a.length === b.length && timingSafeEqual(a, b);
}

/** Protege rotas privilegiadas com o header X-Admin-Token (valor em ADMIN_TOKEN). */
module.exports = (req, res, next) => {
  if (!config.adminToken) return next(new ForbiddenError(MESSAGES.ADMIN_DISABLED));
  const token = req.get('X-Admin-Token') || '';
  if (!tokensMatch(token, config.adminToken)) return next(new UnauthorizedError(MESSAGES.ADMIN_INVALID_TOKEN));
  next();
};
