'use strict';

const { validateCheckout } = require('../validators/checkoutValidator');
const checkoutService = require('../services/checkoutService');
const { MESSAGES } = require('../utils/constants');

async function checkout(req, res) {
  const input = validateCheckout(req.body);
  const { enrollmentId } = await checkoutService.checkout(input);
  res.status(200).json({ msg: MESSAGES.CHECKOUT_SUCCESS, enrollment_id: enrollmentId });
}

module.exports = { checkout };
