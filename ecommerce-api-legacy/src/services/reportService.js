'use strict';

const db = require('../database/connection');
const { PAYMENT_STATUS } = require('../utils/constants');

const REPORT_SQL = `
    SELECT c.id       AS course_id,
           c.title    AS course,
           e.id       AS enrollment_id,
           u.name     AS student,
           p.amount   AS amount,
           p.status   AS status
    FROM courses c
    LEFT JOIN enrollments e ON e.course_id = c.id
    LEFT JOIN users       u ON u.id = e.user_id
    LEFT JOIN payments    p ON p.enrollment_id = e.id
    ORDER BY c.id, e.id`;

/** Relatório financeiro: [{ course, revenue, students: [{ student, paid }] }] em uma única query. */
async function financialReport() {
    const rows = await db.all(REPORT_SQL);
    const byCourse = new Map();

    for (const row of rows) {
        if (!byCourse.has(row.course_id)) {
            byCourse.set(row.course_id, { course: row.course, revenue: 0, students: [] });
        }
        if (row.enrollment_id === null) continue;

        const entry = byCourse.get(row.course_id);
        const paid = row.amount || 0;
        if (row.status === PAYMENT_STATUS.PAID) entry.revenue += paid;
        entry.students.push({ student: row.student || 'Unknown', paid });
    }

    return Array.from(byCourse.values());
}

module.exports = { financialReport };
