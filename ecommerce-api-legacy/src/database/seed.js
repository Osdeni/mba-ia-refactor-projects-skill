'use strict';

const db = require('./connection');
const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const { PAYMENT_STATUS } = require('../utils/constants');

// Mesmos dados da versão original (usuário leonan@fullcycle.com.br / senha 123, agora com hash).
async function runIfEmpty() {
    const row = await db.get('SELECT COUNT(*) AS total FROM users');
    if (row && row.total > 0) return false;

    await db.withTransaction(async () => {
        const user = await userModel.create({ name: 'Leonan', email: 'leonan@fullcycle.com.br', password: '123' });
        const clean = await courseModel.create({ title: 'Clean Architecture', price: 997.0 });
        await courseModel.create({ title: 'Docker', price: 497.0 });
        const enrollmentId = await enrollmentModel.create(user.id, clean.id);
        await paymentModel.create(enrollmentId, clean.price, PAYMENT_STATUS.PAID);
    });
    return true;
}

module.exports = { runIfEmpty };
