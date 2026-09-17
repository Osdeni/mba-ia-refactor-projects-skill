'use strict';

const router = require('express').Router();
const asyncHandler = require('../middlewares/asyncHandler');
const { checkout } = require('../controllers/checkoutController');

router.post('/checkout', asyncHandler(checkout));

module.exports = router;
