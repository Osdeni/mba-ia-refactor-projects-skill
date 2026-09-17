'use strict';

const db = require('../database/connection');
const { hashPassword, verifyPassword } = require('../utils/crypto');

// Campos públicos: o hash da senha nunca sai do model.

function findById(id) {
  return db.get('SELECT id, name, email FROM users WHERE id = ?', [id]);
}

function findByEmail(email) {
  return db.get('SELECT id, name, email FROM users WHERE email = ?', [email]);
}

async function create({ name, email, password }) {
  const { lastID } = await db.run(
    'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
    [name, email, hashPassword(password)],
  );
  return { id: lastID, name, email };
}

/**
 * Confere as credenciais e faz o upgrade transparente de senhas legadas
 * (texto puro) para o formato scrypt no primeiro acerto.
 */
async function verifyCredentials(email, password) {
  const row = await db.get('SELECT id, name, email, pass FROM users WHERE email = ?', [email]);
  if (!row) return null;
  const { ok, needsUpgrade } = verifyPassword(row.pass, password);
  if (!ok) return null;
  if (needsUpgrade) {
    await db.run('UPDATE users SET pass = ? WHERE id = ?', [hashPassword(password), row.id]);
  }
  return { id: row.id, name: row.name, email: row.email };
}

/** Remove o usuário; matrículas e pagamentos caem em cascata (FK). Retorna linhas afetadas. */
async function deleteById(id) {
  const { changes } = await db.run('DELETE FROM users WHERE id = ?', [id]);
  return changes;
}

module.exports = { findById, findByEmail, create, verifyCredentials, deleteById };
