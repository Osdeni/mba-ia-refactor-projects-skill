'use strict';

const config = require('../config');
const logger = require('../utils/logger');
const { MESSAGES } = require('../utils/constants');

/**
 * Handler central de erros (registrado após as rotas).
 * Mantém o envelope original do projeto: texto puro via res.status(n).send(msg).
 */
// eslint-disable-next-line no-unused-vars
module.exports = (err, req, res, next) => {
  if (err.type === 'entity.parse.failed' || err.type === 'entity.too.large') {
    return res.status(400).send(MESSAGES.BAD_REQUEST);
  }

  const status = Number.isInteger(err.status) ? err.status : 500;
  if (status >= 500) {
    logger.error(`${req.method} ${req.originalUrl} -> ${status}: ${err.message}`, config.debug ? err.stack : undefined);
    return res.status(status).send(config.debug ? err.message : MESSAGES.INTERNAL_ERROR);
  }

  res.status(status).send(err.message);
};
