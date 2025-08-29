import os
import json
import asyncio
import datetime
import time
from aiohttp import web
from estadoGlobal import relojes_conectados, ping_events, tareas_extra
import aiohttp
import uuid
from Funciones.asignarIp import obtener_ip_local
from datetime import datetime
from Funciones.empleados import leer_empleados, guardar_empleados


async def Textr(request):
    print("tarea extra")
    print(tareas_extra)
    return web.json_response({
        "accion": "TareasExtras",
        "Pendientes": tareas_extra
    })
# 📦 Actualizar o crear el json de relojes
def actualizar_reloj_en_json(reloj_id, empleado_id, ip, uuid, estatus):
    print("Entre a actuzlizar json")
    ruta_archivo = "relojes_conectados.json"
    nuevo_reloj = {
        "reloj_id": reloj_id,
        "empleado_id": empleado_id,
        "ip": ip,
        "uuid": uuid,
        "estatus": estatus
    }
    print(nuevo_reloj)
    if not os.path.exists(ruta_archivo):
        with open(ruta_archivo, "w") as archivo:
            json.dump([nuevo_reloj], archivo, indent=4)
        print(f"[JSON] Archivo '{ruta_archivo}' creado con el reloj {reloj_id}")
    else:
        with open(ruta_archivo, "r") as archivo:
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

        with open(ruta_archivo, "w") as archivo:
            json.dump(datos, archivo, indent=4)
        print(f"📡 Estado actualizado: {reloj_id} -> {estatus}")
        print(relojes_conectados)

# 📡 Hacer ping a un reloj específico
async def ping_reloj_ws(reloj_id, timeout=5):
    if reloj_id not in relojes_conectados:
        print(f"⚠️ Reloj {reloj_id} no conectado.")
        return False

    ws = relojes_conectados[reloj_id]["ws"]
    ping_events[reloj_id] = asyncio.Event()

    try:
        await ws.send_str(json.dumps({"accion": "ping"}))
        await asyncio.wait_for(ping_events[reloj_id].wait(), timeout=timeout)
        print(f"✅ Pong recibido correctamente desde {reloj_id}")
        del ping_events[reloj_id]
        return True
    except asyncio.TimeoutError:
        print(f"⏳ Timeout esperando pong desde {reloj_id}")
        del ping_events[reloj_id]
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        del ping_events[reloj_id]
        return False

# 🔒 Protección anti-spam para ping_relojes
ultimo_ping_global = 0
INTERVALO_MINIMO_SEGUNDOS = 60  # Solo permitir un ping global cada 60 segundos

# 🛰️ Endpoint para hacer ping a un reloj
async def endpoint_ping_reloj(request):
    reloj_id = request.match_info["reloj_id"]
    resultado_ping = await ping_reloj_ws(reloj_id)

    if resultado_ping:
        return web.json_response({"reloj_id": reloj_id, "estatus": "conectado"})
    else:
        if reloj_id in relojes_conectados:
            info = relojes_conectados[reloj_id]
            actualizar_reloj_en_json(
                reloj_id=reloj_id,
                empleado_id=info["empleado_id"],
                ip=info["ip"],
                uuid=info.get("uuid", "desconocido"),
                estatus="desconectado"
            )
            relojes_conectados.pop(reloj_id, None)

        return web.json_response({"reloj_id": reloj_id, "estatus": "desconectado"})

# 🛰️ Endpoint para hacer ping a todos los relojes (ahora protegido)
async def endpoint_ping_todos_los_relojes(request):
    global ultimo_ping_global

    ahora = time.time()
    if ahora - ultimo_ping_global < INTERVALO_MINIMO_SEGUNDOS:
        return web.json_response({
            "error": "Ping a todos los relojes permitido solo cada 60 segundos"
        }, status=429)

    ultimo_ping_global = ahora
    print("⚡ Ejecutando ping a todos los relojes...")

    ruta_archivo = "relojes_conectados.json"
    
    if not os.path.exists(ruta_archivo):
        return web.json_response({"error": "Archivo no encontrado"}, status=404)

    with open(ruta_archivo, "r") as archivo:
        try:
            relojes_json = json.load(archivo)
        except json.JSONDecodeError:
            return web.json_response({"error": "JSON malformado"}, status=500)

    resultados = []

    for reloj in relojes_json:
        reloj_id = reloj["reloj_id"]

        if reloj_id in relojes_conectados:
            resultado_ping = await ping_reloj_ws(reloj_id)
            if resultado_ping:
                estatus = "conectado"
            else:
                estatus = "desconectado"
                info = relojes_conectados[reloj_id]
                actualizar_reloj_en_json(
                    reloj_id=reloj_id,
                    empleado_id=info["empleado_id"],
                    ip=info["ip"],
                    uuid=info.get("uuid", "desconocido"),
                    estatus=estatus
                )
                relojes_conectados.pop(reloj_id, None)
        else:
            estatus = "desconectado"
            actualizar_reloj_en_json(
                reloj_id=reloj_id,
                empleado_id=reloj.get("empleado_id", "-"),
                ip=reloj.get("ip", "-"),
                uuid=reloj.get("uuid", "-"),
                estatus=estatus
            )

        resultados.append({
            "reloj_id": reloj_id,
            "estatus": estatus
        })

    return web.json_response(resultados)

# 🛠️ (Pendiente de implementación si quieres usarlo luego)
# 📋 Traducción de días de inglés a español
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

# 📋 Endpoint para tareas de un reloj específico envia tareas a reloj
async def endpoint_tareas_para_reloj(request):
    reloj_id = request.match_info["reloj_id"]
    print(relojes_conectados)
    if reloj_id not in relojes_conectados:
        return web.json_response({"error": f"Reloj {reloj_id} no está conectado"}, status=404)

    print(relojes_conectados[reloj_id])
    #no hay empleado_id
    try:
        empleado_id = int(relojes_conectados[reloj_id]["empleado_id"])
    except (ValueError, TypeError):
        return web.json_response({"error": "Empleado ID no válido o no asignado al reloj"}, status=400)

    time.sleep(2)
    #empleado_id = 2
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados = json.load(f)
    except Exception as e:
        return web.json_response({"error": f"No se pudo leer empleados.json: {str(e)}"}, status=500)

    empleado = next((emp for emp in empleados if emp["id"] == empleado_id), None)
    
    if not empleado:
        return web.json_response({"error": f"Empleado {empleado_id} no encontrado"}, status=404)

    dia_ingles = datetime.now().strftime("%A")
    dia_semana = dia_a_espanol(dia_ingles)
    empleado_id =empleado.get("id")
    tareas_del_dia = empleado.get("tareas_asignadas", {}).get(dia_semana, [])
    print(tareas_del_dia)
    tareas_filtradas = []
    pendiente=False
    i=0
    for tarea in tareas_del_dia:
        if tarea.get("estatus") == 2:
            tareas_filtradas.append({
                "Hora": tarea.get("hora", ""),
                "Tarea": tarea.get("nombre", ""),
                "Estado": "En Progreso" if i <1 else "Pendiente",
                "Tipo": "", 
                "IdEmpleado": empleado_id,
                "TaskID": tarea.get("id", "")
            })
            i+=1
            

    respuesta = {
        "accion": "Pendientes",
        "Comando": "Pendientes",
        "Pendientes": tareas_filtradas
    }
    print(respuesta)
    #´primer elemento en progreso y el resto en Pendiente

    try:
        ws = relojes_conectados[reloj_id]["ws"]
        await ws.send_str(json.dumps(respuesta))
        print(f"📤 Tareas enviadas al reloj {reloj_id}")
    except Exception as e:
        print(f"❌ Error enviando tareas al reloj: {e}")

    return web.json_response(respuesta)



#id empleado actualizas 
async def update_reloj_id(request):
    payload = await request.json()              # <-- lee todo el JSON
    empleado_id = payload.get('empleado_id')
    reloj_id    =  payload.get('reloj_id')
    print(f"Reloj: {reloj_id}, Empleado: {empleado_id}")
    #guarde sus datos en un objeto
    async with aiohttp.ClientSession() as session:
        ip = obtener_ip_local()
        # Hacemos GET (puedes usar .post, put, etc según necesites)
        async with session.get(f"http://{ip}:2298/relojes_conectados.json") as resp:
            data = await resp.json()

    print("Datos recibidos:", data)

    obj = next((item for item in data if item.get("reloj_id") == reloj_id), None)
    if obj is None:
        
        print(f"No existe un objeto con name='{reloj_id}' ")
    else:
        print("Encontrado:", obj)
        obj["empleado_id"] = empleado_id
        print(obj)
        actualizar_reloj_en_json(**obj)

        if reloj_id in relojes_conectados:
            relojes_conectados[reloj_id]["empleado_id"] = empleado_id
            
    return web.json_response({
        "menssje": "reloj asignado correctamente",
        "data": obj
    })


async def asignar_uuid_si_falta(ws, uuid_actual):
    if not uuid_actual or uuid_actual.strip() in ("", "-", "desconocido"):
        nuevo_uuid = f"_{str(uuid.uuid4())[:8]}"
        await ws.send_str(json.dumps({"uuid": nuevo_uuid}))
        print(f"🆕 UUID asignado a : {nuevo_uuid}")
        return nuevo_uuid
    return uuid_actual


async def nuevoRelojId(uuid):
    ruta = "relojes_conectados.json"

    if not os.path.exists(ruta):
        return "reloj1"

    with open(ruta, "r", encoding="utf-8") as file:
        try:
            relojes = json.load(file)
        except json.JSONDecodeError:
            print("⚠️ Error: JSON inválido")
            return "reloj1"
        
        for reloj in relojes:
            if reloj.get("uuid") == uuid:
                print("✅ UUID ya registrado, usando reloj existente:", reloj["reloj_id"])
                return reloj["reloj_id"]

        relojes_validos = [r for r in relojes if r.get("reloj_id", "").startswith("reloj")]

        if not relojes_validos:
            return "reloj1"

        ultimo = relojes_validos[-1]["reloj_id"]
        import re
        match = re.match(r"([a-zA-Z]+)(\d+)", ultimo)
        if match:
            prefijo, numero = match.groups()
            nuevo_id = f"{prefijo}{int(numero)+1}"
            return nuevo_id

        # fallback
        return "reloj1"

# >>> DESASIGNAR RELOJ (NUEVO)
async def desasignar_reloj(request):
    """
    PATCH /relojes/{reloj_id}
    Body JSON: { "empleado_id": "" }   # el body no se usa, pero se acepta por consistencia
    """
    reloj_id     = request.match_info.get("reloj_id")
    ruta_archivo = "relojes_conectados.json"

    if not os.path.exists(ruta_archivo):
        return web.json_response({"error": "Archivo relojes_conectados.json no encontrado"}, status=404)

    # Leer JSON
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            relojes = json.load(f)
    except json.JSONDecodeError:
        return web.json_response({"error": "JSON malformado"}, status=500)

    reloj = next((r for r in relojes if r.get("reloj_id") == reloj_id), None)
    if reloj is None:
        return web.json_response({"error": "Reloj no encontrado"}, status=404)

    # Limpiar empleado_id
    reloj["empleado_id"] = ""

    # Guardar archivo
    try:
        with open(ruta_archivo, "w", encoding="utf-8") as f:
            json.dump(relojes, f, indent=2)
    except Exception as e:
        return web.json_response({"error": f"No se pudo escribir archivo: {e}"}, status=500)

    # Actualizar variable global en memoria
    if reloj_id in relojes_conectados:
        relojes_conectados[reloj_id]["empleado_id"] = ""

    return web.json_response({"mensaje": f"Reloj {reloj_id} desasignado correctamente"})
# <<< DESASIGNAR RELOJ (FIN)


async def tarea_terminada(request):
    print("Hola")
    #Estatus a 0

import json

def obtener_reloj_id_por_uuid(uuid):
    with open("relojes_conectados.json", "r") as f:
        relojes = json.load(f)
        for reloj in relojes:
            if reloj.get("uuid") == uuid:
                return reloj.get("reloj_id")
    return None




async def verificar_tareas_expiradas():
    empleados = leer_empleados()
    hoy_dia = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"][datetime.now().weekday()]
    hora_actual = datetime.now().time()
    cambios = False
    tarea_id = None

    for reloj_id, reloj in relojes_conectados.items():
        empleado_id = reloj.get("empleado_id")
        if not empleado_id:
            continue

        for emp in empleados:
            if str(emp.get("id")) != str(empleado_id):
                continue

            tareas = emp.get("tareas_asignadas", {}).get(hoy_dia, [])

            tareas_ordenadas = sorted(tareas, key=lambda t: datetime.strptime(t["hora"], "%H:%M"))

            for i, tarea in enumerate(tareas_ordenadas):
                if tarea["estatus"] != 2:
                    continue

                hora_tarea = datetime.strptime(tarea["hora"], "%H:%M").time()
                if hora_tarea <= hora_actual:
                    tarea["estatus"] = 3
                    print(f"🔔 Tarea vencida: '{tarea['nombre']}' del empleado {emp['nombre']} (Reloj: {reloj_id}) marcada como EXTRA.")
                    cambios = True
                    tarea_id = tarea["id"]

                    


    if cambios and tarea_id>0:
        guardar_empleados(empleados ) #Guarda las tareas menos la tarea extra que no se completo a tiempo
        print("✅ Se guardaron cambios de tareas expiradas en empleados.json")
        ip=obtener_ip_local()
        url = f"http://{ip}:2298/tareas_reloj/{reloj_id}" #Envia el resto de tareas al empleado actual
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers={"Accept": "application/json"}) as response:
                if response.status == 200:
                    resultado = await response.json()
                    print("POST exitoso:", resultado)
                else:
                    print(f"Error {response.status}: {await response.text()}")
        
        url= f"http://{ip}:2298/tareas_reloj_extra/{reloj_id}"

        payload = {
            "tarea_id": tarea_id,
            "empleado_id": empleado_id
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers={"Accept": "application/json"}) as response:
                if response.status == 200:
                    resultado = await response.json()
                    print("POST exitoso:", resultado)
                else:
                    print(f"Error {response.status}: {await response.text()}")
        
async def enviar_tareas_extra(request):
    print("📨 Enviando tarea extra")

    reloj_id = request.match_info["reloj_id"] #Id del reloj para saber el id del reloj que 
    data = await request.json()
    tarea_id = data.get("tarea_id")
    empleado_id = data.get("empleado_id")
    hoy_dia = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"][datetime.now().weekday()]
    
    # Leer empleados
    try:
        with open("empleados.json", "r", encoding="utf-8") as f:
            empleados = json.load(f)
    except Exception as e:
        return web.json_response({"error": f"No se pudo leer empleados.json: {str(e)}"}, status=500)

    # Buscar la tarea por ID en el día actual
    tarea_encontrada = None
    for empleado in empleados:
        tareas = empleado.get("tareas_asignadas", {}).get(hoy_dia, [])
        for tarea in tareas:
            if tarea["id"] == tarea_id:
                tarea_encontrada = tarea
                break
        if tarea_encontrada:
            break

    if not tarea_encontrada:
        return web.json_response({"error": "Tarea no encontrada"}, status=404)

    # Armar la tarea para enviar
    tarea_para_enviar = {
        "Hora": tarea_encontrada.get("hora", "Na"),
        "Tarea": tarea_encontrada.get("nombre", ""),
        "Estado": "Pendiente", 
        "Tipo": "TareasExtras", 
        "TaskID": tarea_encontrada.get("id", "")
    }
    tareas_extra.append(tarea_para_enviar)
    print(tareas_extra)
    respuesta = {
        "accion": "TareasExtras",
        "Comando": "TareasExtras",
        "Pendientes": tareas_extra
    }

    # Enviar a todos los relojes excepto al que corresponde a reloj_id original
    enviados = 0
    for otro_reloj_id, datos in relojes_conectados.items():
        if otro_reloj_id != reloj_id:
            try:
                ws = datos["ws"]
                await ws.send_str(json.dumps(respuesta))
                print(f"📤 Tarea extra enviada a {otro_reloj_id}")
                enviados += 1
            except Exception as e:
                print(f"❌ Error enviando tarea a {otro_reloj_id}: {e}")

    return web.json_response({"mensaje": f"Tarea extra enviada a {enviados} relojes"})

