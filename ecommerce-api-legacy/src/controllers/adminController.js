'use strict';

const reportService = require('../services/reportService');

async function financialReport(req, res) {
  const report = await reportService.financialReport();
  res.status(200).json(report);
}

module.exports = { financialReport };
