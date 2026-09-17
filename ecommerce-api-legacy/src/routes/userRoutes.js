'use strict';

const router = require('express').Router();
const asyncHandler = require('../middlewares/asyncHandler');
const requireAdmin = require('../middlewares/requireAdmin');
const { remove } = require('../controllers/userController');

router.delete('/:id', requireAdmin, asyncHandler(remove));

module.exports = router;
