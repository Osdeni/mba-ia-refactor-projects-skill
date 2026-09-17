'use strict';

const express = require('express');
const config = require('./config');
const database = require('./database');
const logger = require('./utils/logger');
const routes = require('./routes');
const notFound = require('./middlewares/notFound');
const errorHandler = require('./middlewares/errorHandler');

const app = express();

app.use(express.json());
app.use('/api', routes);
app.use(notFound);
app.use(errorHandler);

async function start() {
    await database.init();
    if (!config.adminToken) {
        logger.warn('ADMIN_TOKEN não definido — rotas administrativas respondem 403');
    }
    return new Promise((resolve) => {
        const server = app.listen(config.port, config.host, () => {
            logger.info(`LMS API rodando em http://${config.host}:${config.port} (${config.env})`);
            resolve(server);
        });
    });
}

if (require.main === module) {
    start().catch((err) => {
        logger.error('Falha ao iniciar a aplicação:', err);
        process.exit(1);
    });
}

module.exports = { app, start };
