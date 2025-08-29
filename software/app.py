import asyncio
import datetime
from datetime import datetime
import time
from aiohttp import web, WSMsgType
import aiohttp
import aiohttp_cors
import os
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dateutil.relativedelta import relativedelta, SU   # próximo domingo 
from Funciones.auth import login, login_post, logout 
from Funciones.empleados import empleados, empleado_id, crear_empleado, eliminar_empleado, actualizar_empleado, users_id, actualizar_estatus_empleado, users, leer_empleados
from Funciones.tareas import tareas, tareas_dia
from Funciones.jsonRelog import leer_empleados, filtrar_tareas_con_estatus, tareas_completada
from Funciones.asignarReloj import  Textr, enviar_tareas_extra, verificar_tareas_expiradas, obtener_reloj_id_por_uuid, actualizar_reloj_en_json, endpoint_ping_reloj, endpoint_ping_todos_los_relojes,endpoint_tareas_para_reloj, update_reloj_id, asignar_uuid_si_falta, nuevoRelojId, desasignar_reloj
from estadoGlobal import relojes_conectados, ping_events  # Variables compartidas
from Funciones.asignarIp import obtener_ip_local

#watchmedo auto-restart --pattern="*.py" --recursive -- python app.py
websockets = set()
connected_clients = [] 

#Seguridad del BackEnd para evitar que los usuarios puedan acceder a pestañas no autorizadas
@web.middleware
async def auth_middleware(request, handler):
    path = request.path

    # Rutas públicas (accesibles sin login)
    rutas_publicas = [
        "/", "/inicio", "/login", "/logout", "/web", "/empleados.json", 
        "/relojes_conectados.json", "/ws", "/ping_reloj", "/ping_relojes"
    ]
    if any(path.startswith(r) for r in rutas_publicas):
        return await handler(request)

    # Leer cookie
    user_cookie = request.cookies.get("usuario")
    if not user_cookie:
        return web.HTTPFound('/inicio')

    try:
        user = json.loads(user_cookie)
    except Exception:
        return web.HTTPFound('/inicio')

    rol = user.get("role")

    # Protección por rol
    if path.startswith("/gestion") or path.startswith("/empleados") or path.startswith("/registrar-equipo"):
        if rol != "administrador":
            return web.HTTPFound('/inicio')

    if path.startswith("/informes") or path.startswith("/general"):
        if rol not in ["administrador", "empleado"]:
            return web.HTTPFound('/inicio')

    return await handler(request)

#Hacer el backup de empleados.json a backup.json par mostrar las tareas terminadas durante 15 dias
# --------------------------- ❶ imports extra ---------------------------

# -----------------------------------------------------------------------

# --------------------------- ❷ rutas de archivo ------------------------
BASE_DIR     = os.getcwd()
EMP_PATH     = os.path.join(BASE_DIR, "empleados.json")
BACKUP_PATH  = os.path.join(BASE_DIR, "backup.json")
# -----------------------------------------------------------------------

dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
hoy = dias[datetime.now().weekday()]

# --------------------------- ❸ función de filtro -----------------------
async def generar_backup():
    """
    Crea backup.json conteniendo SOLO tareas con estatus 0
    """
    try:
        with open(EMP_PATH, "r", encoding="utf-8") as f:
            empleados = json.load(f)

        for emp in empleados:
            for dia, lst in emp.get("tareas_asignadas", {}).items():
                emp["tareas_asignadas"][dia] = [t for t in lst if t.get("estatus") == 0]

        with open(BACKUP_PATH, "w", encoding="utf-8") as f:
            json.dump(empleados, f, ensure_ascii=False, indent=2)

        print("✅  Backup generado:", datetime.now().isoformat(timespec="seconds"))
    except Exception as e:
        print("❌  Error generando backup:", e)
# -----------------------------------------------------------------------

# --------------------------- ❹ endpoint opcional -----------------------
async def endpoint_backup(request):
    """
    GET /backup → fuerza regenerar backup.json ahora mismo
    """
    await generar_backup()
    return web.json_response({"success": True})
# más abajo: app.router.add_get("/backup", endpoint_backup)
# -----------------------------------------------------------------------

# --------------------------- ❺ programar tarea ------------------------

async def startup_scheduler(app):
    scheduler = AsyncIOScheduler()

    hoy = datetime.now()
    prox_domingo = (
        hoy + relativedelta(weekday=SU(+1))
    ).replace(hour=0, minute=0, second=0, microsecond=0)

    scheduler.add_job(
        generar_backup,
        trigger="interval",
        weeks=2,
        next_run_time=prox_domingo
    )

    # 👇 Agrega esta línea para ejecutar cada minuto
    scheduler.add_job(
        verificar_tareas_expiradas,
        trigger="interval",
        minutes=1
    )

    scheduler.start()
    print("🗓️  Backup quincenal programado. Primera ejecución:", prox_domingo)
    print("⏱️  Verificador de tareas expiradas programado cada minuto.")

async def websocket_handler(request):
    ws = web.WebSocketResponse(protocols=['arduino'])
    await ws.prepare(request)
    websockets.add(ws)
    connected_clients.append(ws)
    print("Cliente WebSocket conectado")

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                mensaje = json.loads(msg.data)
                accion = mensaje.get("accion")

                if accion == "pong":
                    reloj_id = mensaje.get("reloj_id")
                    if reloj_id in ping_events:
                        ping_events[reloj_id].set()
                        continue

                if accion == "Pruebita":
                    print("Hola las acciones y Ms.type estan funcionando correctamente")
                    print(mensaje)
                    
                    empleado_id = ""
                    ip = request.remote
                    uuid = await asignar_uuid_si_falta(ws, mensaje.get("uuid"))
                    reloj_id = await nuevoRelojId(uuid)

                    print(reloj_id)
                    print("fak")
                    relojes_conectados[reloj_id] = {
                        "ws": ws,
                        "ip": ip,
                        "reloj_id": reloj_id,
                        "empleado_id": empleado_id,
                        "uuid": uuid,
                        "last_seen": time.time()
                    }

                    print(f"Reloj {reloj_id} conectado desde IP {ip} con empleado {empleado_id}")

                    await ws.send_str(json.dumps({
                        "tipo": "motherfoker",
                        "empleado_id": empleado_id
                    }))

                    actualizar_reloj_en_json(
                        reloj_id=reloj_id,
                        empleado_id=empleado_id,
                        ip=ip,
                        uuid=uuid,
                        estatus="conectado"
                    )

                elif accion == "Desconexion":
                    reloj_id = mensaje["reloj_id"]
                    uuid = mensaje.get("uuid")
                    print(f"🔌 Reloj {reloj_id} notificó desconexión")
                    if reloj_id in relojes_conectados:
                        info = relojes_conectados[reloj_id]
                        actualizar_reloj_en_json(
                            reloj_id=reloj_id,
                            empleado_id=info["empleado_id"],
                            ip=info["ip"],
                            uuid=uuid,
                            estatus="desconectado"
                        )
                        relojes_conectados.pop(reloj_id, None)

                elif accion == "solicitar_tareas_extra":
                    tareas_extra = filtrar_tareas_con_estatus()
                    await ws.send_str(json.dumps({
                        "tipo": "tareas_extra",
                        "data": tareas_extra
                    }))

                elif accion == "conectar_reloj":
                    reloj_id = mensaje["reloj_id"]
                    empleado_id = mensaje.get("empleado_id")
                    ip = request.remote
                    relojes_conectados[reloj_id] = {
                        "ws": ws,
                        "ip": ip,
                        "empleado_id": empleado_id,
                        "last_seen": time.time()
                    }
                    print(f"Reloj {reloj_id} conectado desde IP {ip} con empleado {empleado_id}")

                elif accion == "tarea_terminada":
                    time.sleep(2)
                    #terminar_tarea(mensaje)
                    tarea = mensaje["Tarea"]
                    empleado = mensaje["Empleado"]
                    tareaId = mensaje["TareaId"]
                    uuid = mensaje["uuid"]
                    reloj_id= obtener_reloj_id_por_uuid(uuid)
                    print(f"Empleado {empleado} terminó tarea {tareaId}- {tarea}")
                    ip=obtener_ip_local()
                    #empleado vacio entra en tarea extra
                    url = f"http://{ip}:2298/empleados/{empleado}"
                    

                    data= {
                        "tareas_asignadas": {
                            f"{hoy}": [
                                {
                                    "id": tareaId,
                                    "estatus": 0
                                }
                            ]
                        }
                    }
                    async with aiohttp.ClientSession() as session:
                        async with session.patch(url, json=data) as response:
                            if response.status == 200:
                                resultado = await response.json()
                                print("PATCH exitoso:", resultado)
                            else:
                                print(f"Error {response.status}: {await response.text()}")
                    url = f"http://{ip}:2298/tareas_reloj/{reloj_id}"
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, headers={"Accept": "application/json"}) as response:
                            if response.status == 200:
                                resultado = await response.json()
                                print("POST exitoso:", resultado)
                            else:
                                print(f"Error {response.status}: {await response.text()}")

                elif accion == "tarea_extra":
                    tarea = mensaje["Tarea"]
                    tareaId = mensaje["TareaId"]
                    uuid = mensaje["uuid"]
                    reloj_id= obtener_reloj_id_por_uuid(uuid)
                    empleado_id = relojes_conectados[reloj_id]["empleado_id"]
                    
                    print(f"Empleado {empleado_id} terminó tarea {tareaId}- {tarea}")
                    ip=obtener_ip_local()
                    url=f"http://{ip}:2298/empleados/{empleado_id}"
                    #insertar tarea y poner id 4
                    obj= {

                        "tareas_asignadas": {
                            hoy: [
                                {
                                "nombre": tarea,
                                "NewId": tareaId,
                                "estatus": 4
                                }
                            ]
                            }

                        }
                    async with aiohttp.ClientSession() as session:
                        async with session.patch(url, json=obj) as response:
                            if response.status == 200:
                                resultado = await response.json()
                                print("PATCH exitoso:", resultado)
                            else:
                                print(f"Error {response.status}: {await response.text()}")
                    #Sacar de la lsita tareas_extra
                    tareas_extra = [t for t in tareas_extra if t.get("TaskID") != tareaId]

    finally:   
        websockets.remove(ws)
        print("Cliente WebSocket desconectado")

        if ws in connected_clients:
            connected_clients.remove(ws)
            print('Cliente desconectado')

        for r_id, info in relojes_conectados.items():
            if info["ws"] == ws:
                print(f"🛑 Reloj {r_id} se ha desconectado")
                actualizar_reloj_en_json(
                    reloj_id=r_id,
                    empleado_id=info["empleado_id"],
                    ip=info["ip"],
                    uuid=info.get("uuid", "desconocido"),
                    estatus="desconectado"
                )
                break

    return ws

# === Vistas ===
async def home(request):
    raise web.HTTPFound('/login')

async def inicio(request):
    return web.FileResponse('./web/Home/home.html')

async def general(request):
    return web.FileResponse('./web/General/general.html')

async def gestion(request):
    return web.FileResponse('./web/gestion/gestion.html')

async def informes(request):
    return web.FileResponse('./web/informes/informes.html')

async def obtener_json(request):
    json_path = os.path.join(os.getcwd(), 'empleados.json')
    if os.path.exists(json_path):
        return web.FileResponse(json_path)
    return web.Response(status=404, text="Archivo empleados.json no encontrado.")

async def obtener_relojes_json(request):
    json_path = os.path.join(os.getcwd(), 'relojes_conectados.json')
    if os.path.exists(json_path):
        return web.FileResponse(json_path)
    return web.Response(status=404, text="Archivo relojes_conectados.json no encontrado.")

async def registrar_equipo(request):
    return web.FileResponse('./web/gestion/Registrar Equipo/registrarEquipo.html')

async def enviar_a_todos(mensaje):
    mensaje_str = json.dumps(mensaje)
    for client in connected_clients:
        if not client.closed:
            await client.send_str(mensaje_str)

async def obtener_backup_json(request):
    json_path = os.path.join(os.getcwd(), 'backup.json')
    if os.path.exists(json_path):
        return web.FileResponse(json_path)
    return web.Response(status=404, text="Archivo backup.json no encontrado.")


# === Configuración de la app ===
app = web.Application(client_max_size=10 * 1024 * 1024, middlewares=[auth_middleware])
app.on_startup.append(startup_scheduler)
print(relojes_conectados)

app.router.add_get('/', home)
app.router.add_get('/inicio', inicio)
app.router.add_get('/login', login)
app.router.add_get('/logout', logout)
app.router.add_get('/gestion', gestion)
app.router.add_get('/informes', informes)
app.router.add_get('/general', general)
app.router.add_get('/empleados', empleados)
app.router.add_get('/empleados/{id}', empleado_id)
app.router.add_get('/user/{id}', users_id)
app.router.add_post('/empleados', crear_empleado)
app.router.add_post('/login', login_post)
app.router.add_delete('/empleados/{id}', eliminar_empleado)
app.router.add_patch('/empleados/{id}', actualizar_empleado)
app.router.add_patch('/empleados/{id}/estatus', actualizar_estatus_empleado)
app.router.add_get('/users', users)
app.router.add_get('/textra', Textr)


app.router.add_get('/tareas', tareas)
app.router.add_get('/tareas/{id}/{dia}', tareas_dia)
app.router.add_get('/empleados.json', obtener_json)
app.router.add_get('/relojes_conectados.json', obtener_relojes_json)
app.router.add_get('/registrar-equipo', registrar_equipo)
app.router.add_get('/ping_relojes', endpoint_ping_todos_los_relojes)
#app.router.add_get('/relojes_asign/{empleado_id}', asignar_esmpleado)
app.router.add_get('/ws', websocket_handler)
app.router.add_get('/ping_reloj/{reloj_id}', endpoint_ping_reloj)
app.router.add_static('/web', path='./web', name='web')
app.router.add_post('/tareas_reloj/{reloj_id}', endpoint_tareas_para_reloj)

app.router.add_patch('/update_reloj_id/{reloj_id}', update_reloj_id)
app.router.add_patch('/relojes/{reloj_id}', desasignar_reloj) 
app.router.add_post('/tareas_reloj_extra/{reloj_id}', enviar_tareas_extra)
app.router.add_get('/backup', endpoint_backup)   # ⬅️ entre los add_get
app.router.add_get('/backup.json', obtener_backup_json)


# CORS
cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
    )
})
for route in list(app.router.routes()):
    cors.add(route)

if __name__ == "__main__":
    web.run_app(app, host= obtener_ip_local(), port=2298)
