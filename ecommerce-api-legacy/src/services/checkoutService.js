'use strict';

const { withTransaction } = require('../database/connection');
const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');
const paymentGateway = require('./paymentGateway');
const logger = require('../utils/logger');
const { NotFoundError, PaymentDeniedError, ValidationError } = require('../errors/AppError');
const { PAYMENT_STATUS, MESSAGES } = require('../utils/constants');

async function findOrCreateUser({ name, email, password }) {
  const existing = await userModel.findByEmail(email);
  if (existing) return existing;
  // Segurança: não há mais senha padrão para novos usuários.
  if (!password) throw new ValidationError(MESSAGES.BAD_REQUEST);
  return userModel.create({ name, email, password });
}

/**
 * Caso de uso de checkout: curso ativo → usuário (existente ou novo) → cobrança →
 * matrícula + pagamento + auditoria em uma única transação.
 */
async function checkout({ name, email, password, courseId, card }) {
  const course = await courseModel.findActiveById(courseId);
  if (!course) throw new NotFoundError(MESSAGES.COURSE_NOT_FOUND);

  const user = await findOrCreateUser({ name, email, password });

  const status = paymentGateway.charge({ card, amount: course.price });
  if (status === PAYMENT_STATUS.DENIED) throw new PaymentDeniedError(MESSAGES.PAYMENT_DENIED);

  const enrollmentId = await withTransaction(async () => {
    const id = await enrollmentModel.create(user.id, course.id);
    await paymentModel.create(id, course.price, status);
    await auditLogModel.record(`Checkout curso ${course.id} por ${user.id}`);
    return id;
  });

  logger.info(`Checkout concluído: usuário ${user.id}, curso "${course.title}", matrícula ${enrollmentId}`);
  return { enrollmentId };
}

module.exports = { checkout };
