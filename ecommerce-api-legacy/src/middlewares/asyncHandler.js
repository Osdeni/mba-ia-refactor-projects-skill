'use strict';

/** Express 4 não propaga rejeições de handlers async; este wrapper encaminha ao errorHandler. */
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
