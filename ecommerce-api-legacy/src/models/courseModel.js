'use strict';

const db = require('../database/connection');

async function findActiveById(id) {
    return db.get('SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1', [id]);
}

async function create({ title, price, active = true }) {
    const { lastID } = await db.run(
        'INSERT INTO courses (title, price, active) VALUES (?, ?, ?)',
        [title, price, active ? 1 : 0]
    );
    return { id: lastID, title, price, active: active ? 1 : 0 };
}

module.exports = { findActiveById, create };
