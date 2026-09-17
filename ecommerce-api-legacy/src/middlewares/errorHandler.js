'use strict';

const config = require('../config');
const logger = require('../utils/logger');
const { MESSAGES } = require('../utils/constants');

// Envelope de erro do projeto: texto puro (res.send), como na versão original.
// eslint-disable-next-line no-unused-vars
module.exports = (err, req, res, next) => {
    if (err && err.type === 'entity.parse.failed') {
        return res.status(400).send(MESSAGES.BAD_REQUEST);
    }

    const status = Number.isInteger(err && err.status) ? err.status : 500;
    if (status >= 500) {
        logger.error(`${req.method} ${req.originalUrl} falhou:`, config.debug ? err : (err && err.message));
        return res.status(status).send(MESSAGES.INTERNAL_ERROR);
    }
    return res.status(status).send(err.message);
};
