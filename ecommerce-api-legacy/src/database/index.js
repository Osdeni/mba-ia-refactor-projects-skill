'use strict';

const schema = require('./schema');
const seed = require('./seed');

/** Cria o schema e popula os seeds quando o banco está vazio. */
async function initDatabase() {
  await schema.createTables();
  return seed.runIfEmpty();
}

module.exports = { initDatabase };
