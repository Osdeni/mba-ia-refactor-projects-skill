'use strict';

const express = require('express');
const config = require('./config');
const logger = require('./utils/logger');
const { initDatabase } = require('./database');
const apiRoutes = require('./routes');
const notFound = require('./middlewares/notFound');
const errorHandler = require('./middlewares/errorHandler');

/** Composition root: monta a aplicação sem subir o servidor (útil para testes). */
function createApp() {
  const app = express();
  app.disable('x-powered-by');
  app.use(express.json({ limit: config.jsonBodyLimit }));

  app.use('/api', apiRoutes);

  app.use(notFound);
  app.use(errorHandler);
  return app;
}

async function start() {
  for (const warning of config.insecureDefaultWarnings()) logger.warn(warning);

  await initDatabase();
  const app = createApp();

  return new Promise((resolve) => {
    const server = app.listen(config.port, config.host, () => {
      logger.info(`LMS API rodando em http://${config.host}:${config.port} (${config.env})`);
      resolve(server);
    });
  });
}

process.on('unhandledRejection', (reason) => {
  logger.error('unhandledRejection', reason);
});

if (require.main === module) {
  start().catch((err) => {
    logger.error(`Falha ao iniciar a aplicação: ${err.message}`);
    process.exit(1);
  });
}

module.exports = { createApp, start };
