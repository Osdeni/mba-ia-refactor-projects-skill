'use strict';

const sqlite3 = require('sqlite3');
const config = require('../config');

// Conexão única (SQLite em memória por padrão) com API promisificada.
const db = new sqlite3.Database(config.dbFile);

function run(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function onRun(err) {
            if (err) return reject(err);
            return resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

function get(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
}

function all(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
}

function exec(sql) {
    return new Promise((resolve, reject) => {
        db.exec(sql, (err) => (err ? reject(err) : resolve()));
    });
}

async function withTransaction(fn) {
    await run('BEGIN');
    try {
        const result = await fn();
        await run('COMMIT');
        return result;
    } catch (err) {
        await run('ROLLBACK').catch(() => {});
        throw err;
    }
}

function close() {
    return new Promise((resolve, reject) => db.close((err) => (err ? reject(err) : resolve())));
}

module.exports = { run, get, all, exec, withTransaction, close };
