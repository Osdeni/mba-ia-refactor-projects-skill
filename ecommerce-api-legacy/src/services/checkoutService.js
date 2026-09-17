'use strict';

const db = require('../database/connection');
const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');
const paymentGateway = require('./paymentGateway');
const logger = require('../utils/logger');
const { NotFoundError, ValidationError } = require('../errors/AppError');
const { PAYMENT_STATUS, MESSAGES } = require('../utils/constants');

/**
 * Caso de uso: checkout de um curso.
 * findActiveCourse → findOrCreateUser → cobrar → transação (matrícula + pagamento + auditoria).
 */
async function checkout({ name, email, password, courseId, card }) {
    const course = await courseModel.findActiveById(courseId);
    if (!course) throw new NotFoundError(MESSAGES.COURSE_NOT_FOUND);

    const user = (await userModel.findByEmail(email)) || (await userModel.create({ name, email, password }));

    const status = paymentGateway.charge(card, course.price);
    if (status === PAYMENT_STATUS.DENIED) throw new ValidationError(MESSAGES.PAYMENT_DENIED);

    const enrollmentId = await db.withTransaction(async () => {
        const id = await enrollmentModel.create(user.id, course.id);
        await paymentModel.create(id, course.price, status);
        await auditLogModel.record(`Checkout curso ${course.id} por ${user.id}`);
        return id;
    });

    logger.info(`Checkout concluído: usuário ${user.id}, curso ${course.id}, matrícula ${enrollmentId}`);
    return { enrollmentId };
}

module.exports = { checkout };
