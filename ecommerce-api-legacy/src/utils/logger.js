'use strict';

const config = require('../config');

const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };
const threshold = LEVELS[config.logLevel] !== undefined ? LEVELS[config.logLevel] : LEVELS.info;

function write(level, args) {
    if (LEVELS[level] > threshold) return;
    const line = `${new Date().toISOString()} ${level.toUpperCase()}`;
    const sink = level === 'error' ? console.error : level === 'warn' ? console.warn : console.log;
    sink(line, ...args);
}

/** Mascara um número de cartão: nunca logar o PAN completo. */
function maskCard(card) {
    const digits = String(card || '');
    return `****${digits.slice(-4)}`;
}

module.exports = {
    error: (...args) => write('error', args),
    warn: (...args) => write('warn', args),
    info: (...args) => write('info', args),
    debug: (...args) => write('debug', args),
    maskCard,
};
