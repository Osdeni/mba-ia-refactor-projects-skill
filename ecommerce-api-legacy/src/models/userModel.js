'use strict';

const db = require('../database/connection');
const { hashPassword, verifyPassword } = require('../utils/crypto');

// Campos públicos: o hash da senha nunca sai do model.
const PUBLIC_FIELDS = ['id', 'name', 'email'];

function toPublic(row) {
    if (!row) return null;
    return PUBLIC_FIELDS.reduce((out, field) => ({ ...out, [field]: row[field] }), {});
}

async function findById(id) {
    return toPublic(await db.get('SELECT id, name, email FROM users WHERE id = ?', [id]));
}

async function findByEmail(email) {
    return toPublic(await db.get('SELECT id, name, email FROM users WHERE email = ?', [email]));
}

async function create({ name, email, password }) {
    const { lastID } = await db.run(
        'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        [name, email, hashPassword(password)]
    );
    return { id: lastID, name, email };
}

/** Confere a senha e faz upgrade transparente de registros legados (texto puro). */
async function checkPassword(email, password) {
    const row = await db.get('SELECT id, pass FROM users WHERE email = ?', [email]);
    if (!row) return false;
    const { ok, needsUpgrade } = verifyPassword(row.pass, password);
    if (ok && needsUpgrade) {
        await db.run('UPDATE users SET pass = ? WHERE id = ?', [hashPassword(password), row.id]);
    }
    return ok;
}

/** Remove o usuário; matrículas e pagamentos caem em cascata (FK). Retorna linhas afetadas. */
async function remove(id) {
    const { changes } = await db.run('DELETE FROM users WHERE id = ?', [id]);
    return changes;
}

module.exports = { findById, findByEmail, create, checkPassword, remove, toPublic };
