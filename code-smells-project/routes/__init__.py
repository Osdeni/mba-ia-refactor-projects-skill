from routes import pedido_routes, produto_routes, relatorio_routes, sistema_routes, usuario_routes

BLUEPRINTS = (
    produto_routes.bp,
    usuario_routes.bp,
    pedido_routes.bp,
    relatorio_routes.bp,
    sistema_routes.bp,
)


def register_blueprints(app):
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
