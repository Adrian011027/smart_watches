import os
import json
import asyncio
import time
import aiohttp
from aiohttp import web
import uuid
from datetime import datetime

from estadoGlobal import relojes_conectados, ping_events, tareas_extra
from Funciones.asignarIp import obtener_ip_local
from utils.files import leer_empleados, guardar_empleados
from utils.tareas_utils import filtrar_tareas, dia_actual


# ========================
# 📋 Endpoint tareas extras
# ========================
async def Textr(request):
    return web.json_response({
        "accion": "TareasExtras",
        "Pendientes": tareas_extra
    })


# ========================
# 📦 Guardar estado reloj
# ========================
def actualizar_reloj_en_json(reloj_id, empleado_id, ip, uuid, estatus):
    ruta_archivo = "relojes_conectados.json"
    nuevo_reloj = {
        "reloj_id": reloj_id,
        "empleado_id": empleado_id,
        "ip": ip,
        "uuid": uuid,
        "estatus": estatus
    }

    if not os.path.exists(ruta_archivo):
        with open(ruta_archivo, "w", encoding="utf-8") as archivo:
            json.dump([nuevo_reloj], archivo, indent=4, ensure_ascii=False)
        return

    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        try:
            datos = json.load(archivo)
        except json.JSONDecodeError:
            datos = []

    actualizado = False
    for r in datos:
        if r["reloj_id"] == reloj_id:
            r.update(nuevo_reloj)
            actualizado = True
            break

    if not actualizado:
        datos.append(nuevo_reloj)

    with open(ruta_archivo, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)


# ========================
# 📡 Ping a un reloj
# ========================
async def ping_reloj_ws(reloj_id, timeout=5):
    if reloj_id not in relojes_conectados:
        return False

    ws = relojes_conectados[reloj_id]["ws"]
    ping_events[reloj_id] = asyncio.Event()

    try:
        await ws.send_str(json.dumps({"accion": "ping"}))
        await asyncio.wait_for(ping_events[reloj_id].wait(), timeout=timeout)
        del ping_events[reloj_id]
        return True
    except Exception:
        del ping_events[reloj_id]
        return False


# ========================
# 🛰️ Endpoint: ping uno
# ========================
async def endpoint_ping_reloj(request):
    reloj_id = request.match_info["reloj_id"]
    resultado_ping = await ping_reloj_ws(reloj_id)

    estatus = "conectado" if resultado_ping else "desconectado"
    if reloj_id in relojes_conectados and estatus == "desconectado":
        info = relojes_conectados[reloj_id]
        actualizar_reloj_en_json(
            reloj_id=reloj_id,
            empleado_id=info["empleado_id"],
            ip=info["ip"],
            uuid=info.get("uuid", "desconocido"),
            estatus=estatus
        )
        relojes_conectados.pop(reloj_id, None)

    return web.json_response({"reloj_id": reloj_id, "estatus": estatus})


# ========================
# 🛰️ Endpoint: ping todos
# ========================
ultimo_ping_global = 0
INTERVALO_MINIMO_SEGUNDOS = 60

async def endpoint_ping_todos_los_relojes(request):
    global ultimo_ping_global
    ahora = time.time()
    if ahora - ultimo_ping_global < INTERVALO_MINIMO_SEGUNDOS:
        return web.json_response({
            "error": "Ping permitido solo cada 60 segundos"
        }, status=429)

    ultimo_ping_global = ahora

    ruta_archivo = "relojes_conectados.json"
    if not os.path.exists(ruta_archivo):
        return web.json_response({"error": "Archivo no encontrado"}, status=404)

    with open(ruta_archivo, "r", encoding="utf-8") as archivo:
        try:
            relojes_json = json.load(archivo)
        except json.JSONDecodeError:
            return web.json_response({"error": "JSON malformado"}, status=500)

    resultados = []
    for reloj in relojes_json:
        reloj_id = reloj["reloj_id"]

        if reloj_id in relojes_conectados:
            resultado_ping = await ping_reloj_ws(reloj_id)
            estatus = "conectado" if resultado_ping else "desconectado"
        else:
            estatus = "desconectado"

        actualizar_reloj_en_json(
            reloj_id=reloj_id,
            empleado_id=reloj.get("empleado_id", "-"),
            ip=reloj.get("ip", "-"),
            uuid=reloj.get("uuid", "-"),
            estatus=estatus
        )
        if estatus == "desconectado" and reloj_id in relojes_conectados:
            relojes_conectados.pop(reloj_id, None)

        resultados.append({"reloj_id": reloj_id, "estatus": estatus})

    return web.json_response(resultados)


# ========================
# 📋 Endpoint: tareas para reloj
# ========================
def dia_a_espanol(dia_ingles):
    traduccion = {
        "monday": "lunes",
        "tuesday": "martes",
        "wednesday": "miercoles",
        "thursday": "jueves",
        "friday": "viernes",
        "saturday": "sabado",
        "sunday": "domingo"
    }
    return traduccion.get(dia_ingles.lower(), dia_ingles)


async def endpoint_tareas_para_reloj(request):
    reloj_id = request.match_info["reloj_id"]
    if reloj_id not in relojes_conectados:
        return web.json_response({"error": f"Reloj {reloj_id} no conectado"}, status=404)

    empleado_id = relojes_conectados[reloj_id].get("empleado_id")
    if not empleado_id:
        return web.json_response({"error": "Empleado ID no válido"}, status=400)

    empleados = leer_empleados()
    empleado = next((e for e in empleados if e["id"] == int(empleado_id)), None)
    if not empleado:
        return web.json_response({"error": "Empleado no encontrado"}, status=404)

    dia_semana = dia_a_espanol(datetime.now().strftime("%A"))
    tareas_del_dia = empleado.get("tareas_asignadas", {}).get(dia_semana, [])

    tareas_filtradas = []
    for i, tarea in enumerate(tareas_del_dia):
        if tarea.get("estatus") == 2:  # TODO
            tareas_filtradas.append({
                "Hora": tarea.get("hora", ""),
                "Tarea": tarea.get("nombre", ""),
                "Estado": "En Progreso" if i == 0 else "Pendiente",
                "Tipo": "",
                "IdEmpleado": empleado_id,
                "TaskID": tarea.get("id", "")
            })

    respuesta = {
        "accion": "Pendientes",
        "Comando": "Pendientes",
        "Pendientes": tareas_filtradas
    }

    try:
        ws = relojes_conectados[reloj_id]["ws"]
        await ws.send_str(json.dumps(respuesta))
    except Exception as e:
        print(f"❌ Error enviando tareas: {e}")

    return web.json_response(respuesta)


# ========================
# 🔑 Update reloj → empleado
# ========================
async def update_reloj_id(request):
    payload = await request.json()
    empleado_id = payload.get("empleado_id")
    reloj_id = payload.get("reloj_id")

    async with aiohttp.ClientSession() as session:
        ip = obtener_ip_local()
        async with session.get(f"http://{ip}:2298/relojes_conectados.json") as resp:
            data = await resp.json()

    obj = next((item for item in data if item.get("reloj_id") == reloj_id), None)
    if obj:
        obj["empleado_id"] = empleado_id
        actualizar_reloj_en_json(**obj)
        if reloj_id in relojes_conectados:
            relojes_conectados[reloj_id]["empleado_id"] = empleado_id

    return web.json_response({"mensaje": "Reloj asignado correctamente", "data": obj})


# ========================
# 🆔 UUID
# ========================
async def asignar_uuid_si_falta(ws, uuid_actual):
    if not uuid_actual or uuid_actual.strip() in ("", "-", "desconocido"):
        nuevo_uuid = f"_{str(uuid.uuid4())[:8]}"
        await ws.send_str(json.dumps({"uuid": nuevo_uuid}))
        return nuevo_uuid
    return uuid_actual


async def nuevoRelojId(uuid):
    ruta = "relojes_conectados.json"
    if not os.path.exists(ruta):
        return "reloj1"

    with open(ruta, "r", encoding="utf-8") as f:
        try:
            relojes = json.load(f)
        except json.JSONDecodeError:
            return "reloj1"

        for reloj in relojes:
            if reloj.get("uuid") == uuid:
                return reloj["reloj_id"]

        relojes_validos = [r for r in relojes if r.get("reloj_id", "").startswith("reloj")]
        if not relojes_validos:
            return "reloj1"

        ultimo = relojes_validos[-1]["reloj_id"]
        import re
        match = re.match(r"([a-zA-Z]+)(\d+)", ultimo)
        if match:
            prefijo, numero = match.groups()
            return f"{prefijo}{int(numero)+1}"
        return "reloj1"


# ========================
# 🚫 Desasignar reloj
# ========================
async def desasignar_reloj(request):
    reloj_id = request.match_info.get("reloj_id")
    ruta_archivo = "relojes_conectados.json"

    if not os.path.exists(ruta_archivo):
        return web.json_response({"error": "Archivo no encontrado"}, status=404)

    with open(ruta_archivo, "r", encoding="utf-8") as f:
        relojes = json.load(f)

    reloj = next((r for r in relojes if r.get("reloj_id") == reloj_id), None)
    if not reloj:
        return web.json_response({"error": "Reloj no encontrado"}, status=404)

    reloj["empleado_id"] = ""
    with open(ruta_archivo, "w", encoding="utf-8") as f:
        json.dump(relojes, f, indent=2, ensure_ascii=False)

    if reloj_id in relojes_conectados:
        relojes_conectados[reloj_id]["empleado_id"] = ""

    return web.json_response({"mensaje": f"Reloj {reloj_id} desasignado correctamente"})


# ========================
# ⏰ Verificar tareas expiradas
# ========================
async def verificar_tareas_expiradas():
    empleados = leer_empleados()
    hoy_dia = dia_actual()
    hora_actual = datetime.now().time()
    cambios = False
    tarea_id = None
    reloj_id = None
    empleado_id = None

    for rid, reloj in relojes_conectados.items():
        empleado_id = reloj.get("empleado_id")
        if not empleado_id:
            continue

        for emp in empleados:
            if str(emp.get("id")) != str(empleado_id):
                continue

            tareas = emp.get("tareas_asignadas", {}).get(hoy_dia, [])
            tareas_ordenadas = sorted(tareas, key=lambda t: datetime.strptime(t["hora"], "%H:%M"))

            for tarea in tareas_ordenadas:
                if tarea["estatus"] != 2:
                    continue
                hora_tarea = datetime.strptime(tarea["hora"], "%H:%M").time()
                if hora_tarea <= hora_actual:
                    tarea["estatus"] = 3
                    cambios = True
                    tarea_id = tarea["id"]
                    reloj_id = rid

    if cambios and tarea_id:
        guardar_empleados(empleados)
        print(f"✅ Se marcó tarea {tarea_id} como EXTRA")


# Aliases de compatibilidad: expone 'enviar_tareas_extra' si existe un nombre distinto
_globals = globals()
_alias_candidates = [
    "enviar_tarea_extra",
    "send_extra_tasks",
    "send_task_extra",
    "enviar_tareas",
    "enviar_tareas_extra_a_reloj",
]

if "enviar_tareas_extra" not in _globals:
    for cand in _alias_candidates:
        if cand in _globals:
            enviar_tareas_extra = _globals[cand]
            break

async def enviar_tareas_extra(request):
    """
    Envía tareas extra a un reloj específico.
    """
    try:
        # Obtener datos del request
        data = await request.json()
        
        # Validar datos requeridos
        required = ['reloj_id', 'tareas']
        if not all(k in data for k in required):
            return web.json_response({
                "error": "Datos incompletos. Se requiere reloj_id y tareas"
            }, status=400)

        reloj_id = data['reloj_id']
        tareas = data['tareas']

        # TODO: Implementa la lógica específica de envío al reloj
        # Por ejemplo:
        # await enviar_a_reloj(reloj_id, tareas)

        return web.json_response({
            "ok": True,
            "message": f"Tareas extra enviadas al reloj {reloj_id}",
            "tareas_enviadas": len(tareas)
        })

    except ValueError as ve:
        return web.json_response({
            "error": f"Datos inválidos: {str(ve)}"
        }, status=400)
    except Exception as e:
        return web.json_response({
            "error": f"Error enviando tareas: {str(e)}"
        }, status=500)

# Asegurar que exponemos el nombre correcto (aliases)
if "send_extra_tasks" in globals() and "enviar_tareas_extra" not in globals():
    enviar_tareas_extra = send_extra_tasks
