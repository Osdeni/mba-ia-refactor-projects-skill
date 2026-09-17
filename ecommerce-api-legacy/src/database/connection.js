'use strict';

const sqlite3 = require('sqlite3');
const config = require('../config');

const db = new sqlite3.Database(config.dbFile);
db.run('PRAGMA foreign_keys = ON');

/** Executa INSERT/UPDATE/DELETE e resolve `{ lastID, changes }`. */
function run(sql, params = []) {
  return new Promise((resolve, reject) => {
    db.run(sql, params, function onRun(err) {
      if (err) reject(err);
      else resolve({ lastID: this.lastID, changes: this.changes });
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

// A conexão é única; transações são serializadas para que statements de
// requisições concorrentes não se misturem dentro de um BEGIN/COMMIT.
let transactionQueue = Promise.resolve();

function withTransaction(fn) {
  const result = transactionQueue.then(async () => {
    await run('BEGIN');
    try {
      const value = await fn();
      await run('COMMIT');
      return value;
    } catch (err) {
      await run('ROLLBACK').catch(() => {});
      throw err;
    }
  });
  transactionQueue = result.catch(() => {});
  return result;
}

function close() {
  return new Promise((resolve, reject) => {
    db.close((err) => (err ? reject(err) : resolve()));
  });
}

module.exports = { run, get, all, exec, withTransaction, close };
