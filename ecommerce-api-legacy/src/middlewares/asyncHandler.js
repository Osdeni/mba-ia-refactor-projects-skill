'use strict';

// Express 4 não propaga promises rejeitadas: encaminha para o errorHandler.
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
