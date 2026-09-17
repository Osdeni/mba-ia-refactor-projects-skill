'use strict';

const router = require('express').Router();

router.use('/', require('./checkoutRoutes'));   // POST /api/checkout
router.use('/admin', require('./adminRoutes')); // GET  /api/admin/financial-report
router.use('/users', require('./userRoutes'));  // DELETE /api/users/:id

module.exports = router;
