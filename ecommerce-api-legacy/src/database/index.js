'use strict';

const connection = require('./connection');
const schema = require('./schema');
const seed = require('./seed');

async function init() {
    await schema.createTables();
    return seed.runIfEmpty();
}

module.exports = { ...connection, init };
