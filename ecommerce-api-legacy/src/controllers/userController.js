'use strict';

const userModel = require('../models/userModel');
const { validateId } = require('../validators/checkoutValidator');
const { NotFoundError } = require('../errors/AppError');
const { MESSAGES } = require('../utils/constants');

async function remove(req, res) {
  const id = validateId(req.params.id);
  const deleted = await userModel.deleteById(id);
  if (deleted === 0) throw new NotFoundError(MESSAGES.USER_NOT_FOUND);
  res.status(200).send(MESSAGES.USER_DELETED);
}

module.exports = { remove };
