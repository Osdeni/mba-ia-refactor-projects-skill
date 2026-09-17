'use strict';

const { ValidationError } = require('../errors/AppError');
const { MESSAGES } = require('../utils/constants');

function nonEmptyString(value) {
    return typeof value === 'string' && value.trim().length > 0;
}

/**
 * Campos externos (`usr`, `eml`, `pwd`, `c_id`, `card`) fazem parte do contrato da API
 * e são mantidos; internamente usamos nomes descritivos.
 */
function validateCheckout(body) {
    const data = body && typeof body === 'object' && !Array.isArray(body) ? body : {};
    const { usr, eml, pwd, c_id: rawCourseId, card } = data;

    if (!nonEmptyString(usr) || !nonEmptyString(eml) || !nonEmptyString(pwd) || !nonEmptyString(card)) {
        throw new ValidationError(MESSAGES.BAD_REQUEST);
    }
    if (!eml.includes('@')) throw new ValidationError(MESSAGES.BAD_REQUEST);

    const courseId = Number(rawCourseId);
    if (rawCourseId === undefined || rawCourseId === null || rawCourseId === '' || !Number.isInteger(courseId) || courseId <= 0) {
        throw new ValidationError(MESSAGES.BAD_REQUEST);
    }

    return {
        name: usr.trim(),
        email: eml.trim().toLowerCase(),
        password: pwd,
        courseId,
        card: card.trim(),
    };
}

function validateId(raw) {
    const id = Number(raw);
    if (!Number.isInteger(id) || id <= 0) throw new ValidationError(MESSAGES.BAD_REQUEST);
    return id;
}

module.exports = { validateCheckout, validateId };
