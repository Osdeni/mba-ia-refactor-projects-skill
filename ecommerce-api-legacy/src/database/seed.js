'use strict';

const db = require('./connection');
const { hashPassword } = require('../utils/crypto');
const { PAYMENT_STATUS } = require('../utils/constants');

/** Mesmos dados do projeto original; a senha do usuário seed agora é armazenada com hash. */
const SEED_USER = { name: 'Leonan', email: 'leonan@fullcycle.com.br', password: '123' };
const SEED_COURSES = [
  { title: 'Clean Architecture', price: 997.0 },
  { title: 'Docker', price: 497.0 },
];

async function runIfEmpty() {
  const row = await db.get('SELECT COUNT(*) AS n FROM users');
  if (row.n > 0) return false;

  await db.withTransaction(async () => {
    const { lastID: userId } = await db.run(
      'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
      [SEED_USER.name, SEED_USER.email, hashPassword(SEED_USER.password)],
    );
    const courseIds = [];
    for (const course of SEED_COURSES) {
      const { lastID } = await db.run(
        'INSERT INTO courses (title, price, active) VALUES (?, ?, 1)',
        [course.title, course.price],
      );
      courseIds.push(lastID);
    }
    const { lastID: enrollmentId } = await db.run(
      'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
      [userId, courseIds[0]],
    );
    await db.run(
      'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
      [enrollmentId, SEED_COURSES[0].price, PAYMENT_STATUS.PAID],
    );
  });
  return true;
}

module.exports = { runIfEmpty };
