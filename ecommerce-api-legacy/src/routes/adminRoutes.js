'use strict';

const router = require('express').Router();
const asyncHandler = require('../middlewares/asyncHandler');
const requireAdmin = require('../middlewares/requireAdmin');
const { financialReport } = require('../controllers/adminController');

router.use(requireAdmin);
router.get('/financial-report', asyncHandler(financialReport));

module.exports = router;
