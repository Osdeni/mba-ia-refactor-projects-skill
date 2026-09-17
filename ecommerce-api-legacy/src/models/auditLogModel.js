'use strict';

const db = require('../database/connection');

async function record(action) {
  const { lastID } = await db.run('INSERT INTO audit_logs (action) VALUES (?)', [action]);
  return lastID;
}

module.exports = { record };
