'use strict';

const db = require('../database/connection');

function findActiveById(id) {
  return db.get('SELECT id, title, price, active FROM courses WHERE id = ? AND active = 1', [id]);
}

function findAll() {
  return db.all('SELECT id, title, price, active FROM courses ORDER BY id');
}

module.exports = { findActiveById, findAll };
