'use strict';

const { scryptSync, randomBytes, timingSafeEqual } = require('crypto');

const PREFIX = 'scrypt';
const KEY_LENGTH = 32;

/** Gera `scrypt$<salt>$<hash>` com sal aleatório (sem dependências externas). */
function hashPassword(password) {
  const salt = randomBytes(16).toString('hex');
  const hash = scryptSync(String(password), salt, KEY_LENGTH).toString('hex');
  return `${PREFIX}$${salt}$${hash}`;
}

function isModernHash(stored) {
  return typeof stored === 'string' && stored.startsWith(`${PREFIX}$`);
}

/**
 * Verifica a senha contra o valor armazenado.
 * Aceita o formato moderno e, por compatibilidade, senhas legadas em texto puro.
 * Retorna `{ ok, needsUpgrade }` para permitir o re-hash transparente.
 */
function verifyPassword(stored, password) {
  if (typeof stored !== 'string' || stored.length === 0) return { ok: false, needsUpgrade: false };
  if (isModernHash(stored)) {
    const [, salt, hash] = stored.split('$');
    const expected = Buffer.from(hash, 'hex');
    const actual = scryptSync(String(password), salt, KEY_LENGTH);
    return { ok: expected.length === actual.length && timingSafeEqual(expected, actual), needsUpgrade: false };
  }
  const a = Buffer.from(stored);
  const b = Buffer.from(String(password));
  return { ok: a.length === b.length && timingSafeEqual(a, b), needsUpgrade: true };
}

module.exports = { hashPassword, verifyPassword, isModernHash };
