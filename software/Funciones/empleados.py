from aiohttp import web
import aiofiles  
import json
import re
import os
from typing import List

from flask import jsonify
from Funciones.schemas import EmpleadoSchema, EmpleadoUpdateSchema, TareaSchema, DIAS_SEMANA, Users, UsersUpdate
from pydantic import ValidationError, SecretStr

UPLOAD_DIR = "./web/Images/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def leer_empleados():
    archivo_empleados = './empleados.json'
    if os.path.exists(archivo_empleados):
        with open(archivo_empleados, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def guardar_empleados(empleados):
    archivo_empleados = './empleados.json'  
    with open(archivo_empleados, 'w', encoding='utf-8') as f:
        json.dump(empleados, f, indent=2)


def leer_users():
    archivo_users = './Funciones/users.json'
    if os.path.exists(archivo_users):
        with open(archivo_users, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"users": []}  

async def users(request):
    # Llamamos a tu función y devolvemos JSON
    
    users = leer_users()
    print("Users cargados:", users)
    
     
    if users:
        return web.json_response(users)
    return web.json_response({'message': 'Usuario no encontrado'}, status=404)


def guardar_users(users):
    archivo_user = './Funciones/users.json'
    for user in users:
        if isinstance(user.get("password"), SecretStr): #cambia el tipo SecretStr a str
            user["password"] = user["password"].get_secret_value() 

    with open(archivo_user, 'w', encoding='utf-8') as f:
        json.dump({"users": users}, f, indent=2)

#posiblemente eliminar esta funcion en un futuro
def guardar_user(user_data):
    archivo_user = './Funciones/users.json'
    users = leer_users()
    users["users"].append(user_data)
    with open(archivo_user, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2)

#-------------------------------------------------------------------------------#
async def empleados(request):
    return web.json_response(leer_empleados())


async def empleado_id(request):
    empleado_id = int(request.match_info['id'])
    empleado = next((e for e in leer_empleados() if e['id'] == empleado_id), None)
    if empleado:
        return web.json_response(empleado)
    return web.json_response({'message': 'Empleado no encontrado'}, status=404)


async def users_id(request):
    users_id = int(request.match_info['id'])
    users = leer_users()
    print("Users cargados:", users)
    print("Users id:", users_id)
    
    user = next((e for e in users['users'] if isinstance(e, dict) and int(e.get('empleado_id')) == users_id), None)
    
    if user:
        return web.json_response(user)
    return web.json_response({'message': 'Usuario no encontrado'}, status=404)


def limpiar_nombre(nombre):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', nombre)

async def crear_empleado(request):
    print("[INFO] Iniciando creación de empleado...")

    reader = await request.multipart()
    data = {}
    imagen = None
    username = ""

    # Leer los campos
    async for part in reader:
        print(f"[DEBUG] Recibiendo campo: {part.name}")
        try:
            if part.name == "imagen":
                imagen = part
                # Leer todos los bytes de la imagen
                file_content = await imagen.read()
                print(f"[DEBUG] Bytes recibidos: {len(file_content)}")  # Verificar contenido

                if len(file_content) > 0:
                    print("[INFO] Imagen detectada")
                else:
                    print("[ERROR] Imagen vacía después de recibirla")
                    return web.json_response({"error": "La imagen está vacía"}, status=400)

            else:
                field_data = await part.text()
                data[part.name] = field_data
                if part.name == "username":
                    username = field_data
        except ValidationError as e:
            
            print(f"Error de validación en la tarea: {e.errors()}")
    # Validar campos
    if not imagen or not username:
        return web.json_response({"error": "Faltan imagen o username"}, status=400)

    # Guardar la imagen
    filename = f"{username}.jpg"
    filepath = os.path.join(UPLOAD_DIR, filename)
    print(f"[INFO] Guardando imagen como: {filepath}")

    try:
        # Guardar la imagen en chunks (para evitar pérdida de datos)
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(file_content)  # Guardar todo el contenido
            print("[INFO] Imagen guardada correctamente")

        # Verificar si el archivo existe y tiene contenido
        if os.path.exists(filepath):
            print(f"[INFO] Tamaño del archivo guardado: {os.path.getsize(filepath)} bytes")
        else:
            print("[ERROR] La imagen no se guardó correctamente")
            return web.json_response({"error": "Error al guardar la imagen"}, status=500)

    except Exception as e:
        print(f"[ERROR] Excepción al guardar la imagen: {e}")
        return web.json_response({"error": "Error al guardar la imagen"}, status=500)

    # Crear empleado
    empleado = {
        "nombre": data.get("nombre"),
        "puesto": data.get("puesto"),
        "imagen": filename
    }

    user ={
        "username": username,
        "password": data.get("password"),
        "role": data.get("role"),
    }
    empleados = leer_empleados()
    nuevo_id = max([e['id'] for e in empleados], default=0) + 1
    empleado_model = EmpleadoSchema(**empleado)  
    nuevo_empleado = empleado_model.model_dump()  
    nuevo_empleado["id"] = nuevo_id
    empleados.append(nuevo_empleado)
    
    user["empleado_id"]=nuevo_id
    user = Users(**user)
    user_dict = user.model_dump()
    user_dict["password"] = user.password.get_secret_value()

    guardar_empleados(empleados)
    guardar_user(user_dict)
    return web.json_response({"message": "Empleado agregado correctamente", "empleado": empleado}, status=201)

# Eliminar un empleado
async def eliminar_empleado(request):
    id = int(request.match_info['id']) 
    print(id)
    empleados = leer_empleados()
    empleado_index = next((i for i, e in enumerate(empleados) if e['id'] == id), None)
    users = leer_users().get("users", [])
    users_index = next((i for i, e in enumerate(users) if int(e['empleado_id']) == id), None)
    
    if empleado_index is None or users_index is None:
        return web.json_response({'message': 'Empleado/usuario no encontrado'}, status=404)

    empleados.pop(empleado_index)
    users.pop(users_index)
    guardar_empleados(empleados)
    guardar_users(users)
    return web.json_response({'message': 'Empleado eliminado correctamente'})

async def actualizar_empleado(request):
    try:
        empleado_id = int(request.match_info['id'])
        print(f"Obteniendo datos para el empleado con id {empleado_id}")

        content_type = request.headers.get("Content-Type", "")
        print(f"[DEBUG] Content-Type recibido: {content_type}")

        data = {}
        imagen = None
        username = ""

        if content_type.startswith("multipart/"):
            reader = await request.multipart()
            async for part in reader:
                print(f"[DEBUG] Recibiendo campo: {part.name}")
                if part.name == "imagen" or part.filename:
                    imagen = await part.read()
                    if not imagen:
                        return web.json_response({"error": "La imagen está vacía"}, status=400)
                else:
                    try:
                        field_data = await part.text()
                        data[part.name] = field_data
                        if part.name == "username":
                            username = field_data
                    except UnicodeDecodeError:
                        return web.json_response({"error": "Error al decodificar texto"}, status=400)

            if imagen:
                filename = f"{username}.jpg"
                filepath = os.path.join(UPLOAD_DIR, filename)
                async with aiofiles.open(filepath, "wb") as f:
                    await f.write(imagen)
                data["imagen"] = filename

        elif content_type.startswith("application/json"):
            try:
                data = await request.json()
                print(f"[DEBUG] JSON recibido: {data}")
            except:
                return web.json_response({"error": "JSON mal formado"}, status=400)
        else:
            return web.json_response({"error": "Tipo de contenido no soportado"}, status=415)

        # Validaciones
        try:
            datos_actualizados = EmpleadoUpdateSchema(**data)
        except ValidationError as e:
            return web.json_response({"error": "Datos inválidos para empleado", "detail": e.errors()}, status=400)

        ultimos = {
            "username": data.get("username"),
            "password": data.get("password"),
            "role": data.get("role"),
        }
        try:
            datos_user_actualizados = UsersUpdate(**ultimos)
        except ValidationError as e:
            return web.json_response({"error": "Datos inválidos para usuario", "detail": e.errors()}, status=400)

        empleados = leer_empleados()
        users = leer_users()["users"]
        idx_emp = next((i for i, e in enumerate(empleados) if e["id"] == empleado_id), None)
        idx_usr = next((i for i, u in enumerate(users) if u.get("empleado_id") == empleado_id), None)

        if idx_emp is None:
            return web.json_response({"message": "Empleado no encontrado"}, status=404)
        if idx_usr is None:
            return web.json_response({"message": "Usuario no encontrado"}, status=404)

        empleado_actual = empleados[idx_emp]
        user_actual = users[idx_usr]

        # ------------------------------
        # Fusionar tareas_asignadas con actualización por ID
        updates = datos_actualizados.model_dump(exclude_none=True)
        nuevas_tareas = updates.pop("tareas_asignadas", None)

        if nuevas_tareas:
            empleado_actual.setdefault("tareas_asignadas", {})

            # Obtener todos los IDs existentes en este empleado
            ids_existentes = []
            for tareas_dia in empleado_actual["tareas_asignadas"].values():
                for t in tareas_dia:
                    if "id" in t and isinstance(t["id"], int):
                        ids_existentes.append(t["id"])
            next_id = max(ids_existentes, default=0) + 1

            for dia, nuevas_lista in nuevas_tareas.items():
                tareas_dia = empleado_actual["tareas_asignadas"].get(dia, [])

                for nueva in nuevas_lista:
                    if "id" in nueva and nueva["id"] is not None:
                        actualizada = False
                        for existente in tareas_dia:
                            if existente.get("id") == nueva["id"]:
                                existente.update(nueva)  # ✅ Actualiza si ya existe
                                actualizada = True
                                break
                        if not actualizada:
                            tareas_dia.append(nueva)  # 🆕 Agrega si no estaba
                    else:
                        # Si no tiene ID, asigna uno nuevo
                        nueva["id"] = next_id
                        next_id += 1
                        tareas_dia.append(nueva)

                empleado_actual["tareas_asignadas"][dia] = tareas_dia

        # ------------------------------
        # Actualizar otros campos del empleado
        empleado_actual.update(updates)
        user_actual.update(datos_user_actualizados.model_dump(exclude_none=True))

        guardar_empleados(empleados)
        guardar_users(users)

        return web.json_response({
            "message": "Empleado actualizado correctamente",
            "empleado": [empleado_actual, user_actual]
        })

    except Exception as e:
        print(f"[ERROR] Excepción inesperada: {e}")
        import traceback; traceback.print_exc()
        return web.json_response({"error": "Error interno del servidor"}, status=500)

async def actualizar_estatus_empleado(request):
    print("antes")
    id_empleado = request.match_info.get("id")
    print(f"El empleado es {id_empleado}")
    data = await request.json()
    print(data)
    nuevo_estatus = data["tareas_asignadas"]["lunes"][0]["estatus"]
    id_task = data["tareas_asignadas"]["lunes"][0]["id"]
    #obtuve el id del empleado, el estatus y la area 
    print(nuevo_estatus) 
    print(id_task)
    """
        print(f"Actualizando estatus del empleado {id_empleado} a '{nuevo_estatus}'")
        return web.json_response({"mensaje": "Estatus actualizado correctamente"})
    """
    return web.json_response({'message': 'Empleado actualizado correctamente', 'empleado': [id_empleado, id_task]})