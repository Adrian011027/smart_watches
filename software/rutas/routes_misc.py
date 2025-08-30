# rutas/routes_misc.py
from aiohttp import web
from Funciones import views

def setup_misc_routes(app: web.Application):
    """
    Registrar rutas misc y websocket handler.
    """
    async def websocket_handler(request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Guarda la conexión websocket en app si necesitas acceder después
        app['websocket'] = ws
        
        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        # Procesa mensaje aquí
                        await ws.send_json({"status": "ok", "message": "received"})
                    except Exception as e:
                        await ws.send_json({"status": "error", "message": str(e)})
                elif msg.type == web.WSMsgType.ERROR:
                    print(f'ws connection closed with exception {ws.exception()}')
        finally:
            # Limpia la referencia al cerrar
            if 'websocket' in app:
                del app['websocket']
        
        return ws

    async def health(request):
        return web.json_response({"ok": True})

    async def version(request):
        return web.json_response({"version": app.get("version", "1.0.0")})

    # --- Páginas ---
    app.router.add_get("/", views.home)
    app.router.add_get("/inicio", views.inicio)
    app.router.add_get("/general", views.general)
    app.router.add_get("/gestion", views.gestion)
    app.router.add_get("/informes", views.informes)
    app.router.add_get("/registrar-equipo", views.registrar_equipo)

    # --- Archivos JSON ---
    app.router.add_get("/empleados.json", views.obtener_json)
    app.router.add_get("/relojes_conectados.json", views.obtener_relojes_json)
    app.router.add_get("/backup.json", views.obtener_backup_json)

    # --- Websocket ---
    app.router.add_get("/ws", websocket_handler)

    # --- Archivos estáticos ---
    app.router.add_static("/web", path="./web", name="web")

    # --- Health ---
    app.router.add_get("/health", health)
    app.router.add_get("/version", version)
