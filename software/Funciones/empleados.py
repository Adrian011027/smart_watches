from aiohttp import web
from Funciones.schemas import EmpleadoSchema, EmpleadoUpdateSchema, Users, UsersUpdate
from pydantic import ValidationError
from utils.files import leer_empleados, guardar_empleados, leer_users, guardar_users, guardar_user
import aiofiles
import os
import re

UPLOAD_DIR = "./web/Images/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ------------------ Endpoints ------------------

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
    user = next((e for e in users['users'] if int(e.get('empleado_id')) == users_id), None)
    if user:
        return web.json_response(user)
    return web.json_response({'message': 'Usuario no encontrado'}, status=404)

async def users(request):
    return web.json_response(leer_users())

def limpiar_nombre(nombre):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', nombre)

# Crear empleado (subida de imagen incluida)
async def crear_empleado(request):
    """
    Normaliza aliases del campo 'role' antes de validar con Pydantic para evitar
    ValidationError cuando vienen valores como "admin".
    """
    data = await request.json()

    # Normalizar alias comunes para 'role'
    _role_aliases = {
        "admin": "administrador",
        "administrator": "administrador",
        "adm": "administrador",
        "empleado": "empleado",
        "administrador": "administrador",
        "user": "empleado",
    }
    if "role" in data and isinstance(data["role"], str):
        key = data["role"].strip().lower()
        data["role"] = _role_aliases.get(key, data["role"])

    # ...existing code that prepara/valida otros campos...
    # por ejemplo: user = Users(**data)
    # Asegúrate de que la variable 'Users' esté importada desde schemas
    user = Users(**data)

    # ...existing code que guarda el usuario, retorna response, etc...
    # ejemplo de retorno (mantén tu implementación):
    # return web.json_response({"ok": True, "user": user.dict()}, status=201)

async def eliminar_empleado(request):
    id = int(request.match_info['id'])
    empleados = leer_empleados()
    users = leer_users().get("users", [])

    emp_idx = next((i for i, e in enumerate(empleados) if e['id'] == id), None)
    usr_idx = next((i for i, u in enumerate(users) if u['empleado_id'] == id), None)

    if emp_idx is None or usr_idx is None:
        return web.json_response({'message': 'No encontrado'}, status=404)

    empleados.pop(emp_idx)
    users.pop(usr_idx)
    guardar_empleados(empleados)
    guardar_users(users)
    return web.json_response({'message': 'Empleado eliminado correctamente'})

async def actualizar_empleado(request):
    """
    Actualiza los datos de un empleado existente.
    """
    empleado_id = request.match_info.get('id')
    if not empleado_id:
        return web.json_response(
            {"error": "ID de empleado requerido"}, 
            status=400
        )

    try:
        # Obtener datos del request
        data = await request.json()
        
        # Normalizar role si viene en la actualización
        if "role" in data and isinstance(data["role"], str):
            _role_aliases = {
                "admin": "administrador",
                "administrator": "administrador",
                "empleado": "empleado",
            }
            key = data["role"].strip().lower()
            data["role"] = _role_aliases.get(key, data["role"])

        # Validar datos con Pydantic
        from .schemas import Users
        user_update = Users(**data)

        # TODO: Implementa la lógica de actualización en tu base de datos
        # Por ejemplo:
        # await db.empleados.update_one(
        #     {"_id": empleado_id},
        #     {"$set": user_update.dict(exclude_unset=True)}
        # )

        return web.json_response({
            "ok": True,
            "message": f"Empleado {empleado_id} actualizado",
            "data": user_update.dict()
        })

    except ValueError as ve:
        return web.json_response(
            {"error": f"Datos inválidos: {str(ve)}"}, 
            status=400
        )
    except Exception as e:
        return web.json_response(
            {"error": f"Error actualizando empleado: {str(e)}"}, 
            status=500
        )

# Asegurar que el módulo expone la función con el nombre correcto
if "update_empleado" in globals() and "actualizar_empleado" not in globals():
    actualizar_empleado = update_empleado

# Aliases de compatibilidad: si tu módulo define funciones con nombres distintos,
# exponemos nombres esperados por las rutas para evitar ImportError.
# (Esto no sobrescribe funciones existentes con el mismo nombre.)
_globals = globals()
_alias_map = {
    "update_empleado": "actualizar_empleado",
    "modificar_empleado": "actualizar_empleado",
    "actualizar_estatus": "actualizar_estatus_empleado",
    "delete_empleado": "eliminar_empleado",
    "remove_empleado": "eliminar_empleado",
    "get_empleado": "empleado_id",
    "listar_empleados": "empleados",
}

for src, target in _alias_map.items():
    if src in _globals and target not in _globals:
        _globals[target] = _globals[src]
