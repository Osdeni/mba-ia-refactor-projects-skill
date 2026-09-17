'use strict';

const { MESSAGES } = require('../utils/constants');

module.exports = (req, res) => res.status(404).send(MESSAGES.NOT_FOUND);
