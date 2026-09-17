'use strict';

const { ValidationError } = require('../errors/AppError');
const { MESSAGES } = require('../utils/constants');

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function nonEmptyString(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

/**
 * Valida o corpo de POST /api/checkout mantendo os nomes de campo externos
 * (usr, eml, pwd, c_id, card) e a mensagem original "Bad Request".
 */
function validateCheckout(body) {
  const data = body && typeof body === 'object' ? body : {};
  const { usr, eml, pwd, c_id: rawCourseId, card } = data;

  if (!nonEmptyString(usr) || !nonEmptyString(eml) || !nonEmptyString(card)) {
    throw new ValidationError(MESSAGES.BAD_REQUEST);
  }
  if (!EMAIL_RE.test(eml.trim())) throw new ValidationError(MESSAGES.BAD_REQUEST);

  const courseId = Number(rawCourseId);
  if (!Number.isInteger(courseId) || courseId <= 0) throw new ValidationError(MESSAGES.BAD_REQUEST);

  if (pwd !== undefined && pwd !== null && typeof pwd !== 'string') {
    throw new ValidationError(MESSAGES.BAD_REQUEST);
  }

  return {
    name: usr.trim(),
    email: eml.trim().toLowerCase(),
    password: pwd ? pwd : null,
    courseId,
    card: card.replace(/\s+/g, ''),
  };
}

/** Valida um id numérico de rota (`/api/users/:id`). */
function validateId(raw) {
  const id = Number(raw);
  if (!Number.isInteger(id) || id <= 0) throw new ValidationError(MESSAGES.BAD_REQUEST);
  return id;
}

module.exports = { validateCheckout, validateId };
