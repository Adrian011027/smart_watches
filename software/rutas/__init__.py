# rutas/__init__.py
from aiohttp import web

def setup_routes(app: web.Application):
    """
    Importar módulos de rutas DENTRO de la función para evitar ciclos
    entre app.py <-> rutas.
    """
    from .routes_empleados import setup_empleados_routes
    from .routes_auth import setup_auth_routes
    from .routes_tareas import setup_tareas_routes
    from .routes_relojes import setup_relojes_routes
    from .routes_misc import setup_misc_routes

    setup_empleados_routes(app)
    setup_auth_routes(app)
    setup_tareas_routes(app)
    setup_relojes_routes(app)
    setup_misc_routes(app)
