'use strict';

const db = require('../database/connection');

async function create(userId, courseId) {
    const { lastID } = await db.run(
        'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
        [userId, courseId]
    );
    return lastID;
}

module.exports = { create };
