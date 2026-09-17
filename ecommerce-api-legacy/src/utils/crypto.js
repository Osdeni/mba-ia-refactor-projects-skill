'use strict';

const { scryptSync, randomBytes, timingSafeEqual } = require('crypto');

const PREFIX = 'scrypt';
const KEY_LENGTH = 32;

function hashPassword(password) {
    const salt = randomBytes(16).toString('hex');
    const hash = scryptSync(String(password), salt, KEY_LENGTH).toString('hex');
    return `${PREFIX}$${salt}$${hash}`;
}

function safeEqual(a, b) {
    const bufA = Buffer.from(a);
    const bufB = Buffer.from(b);
    return bufA.length === bufB.length && timingSafeEqual(bufA, bufB);
}

/**
 * Verifica a senha. Retorna { ok, needsUpgrade }.
 * Aceita hashes scrypt (formato atual) e senhas legadas em texto puro
 * (bancos criados pela versão anterior), sinalizando upgrade transparente.
 */
function verifyPassword(stored, password) {
    if (!stored) return { ok: false, needsUpgrade: false };
    const [prefix, salt, hash] = String(stored).split('$');
    if (prefix === PREFIX && salt && hash) {
        const candidate = scryptSync(String(password), salt, KEY_LENGTH);
        return { ok: safeEqual(Buffer.from(hash, 'hex'), candidate), needsUpgrade: false };
    }
    return { ok: safeEqual(String(stored), String(password)), needsUpgrade: true };
}

module.exports = { hashPassword, verifyPassword };
