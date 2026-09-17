'use strict';

const router = require('express').Router();
const checkoutRoutes = require('./checkoutRoutes');
const adminRoutes = require('./adminRoutes');
const userRoutes = require('./userRoutes');

router.use('/', checkoutRoutes);   // POST /api/checkout
router.use('/admin', adminRoutes); // GET  /api/admin/financial-report
router.use('/users', userRoutes);  // DELETE /api/users/:id

module.exports = router;
