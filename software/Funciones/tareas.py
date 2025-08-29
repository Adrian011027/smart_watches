from aiohttp import web
import json
import os
from Funciones.schemas import EmpleadoSchema, EmpleadoUpdateSchema, TareaSchema
from pydantic import ValidationError

# Función para leer empleados desde el archivo JSON
def leer_empleados():
    archivo_empleados = './empleados.json'
    if os.path.exists(archivo_empleados):
        with open(archivo_empleados, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Función para guardar empleados en el archivo JSON
def guardar_empleados(empleados):
    archivo_empleados = './empleados.json'
    with open(archivo_empleados, 'w', encoding='utf-8') as f:
        json.dump(empleados, f, indent=2)

# Obtener todos los empleados
async def tareas(request):
    print('Tareas')
    return web.json_response(leer_empleados())
    

# Obtener un empleado por ID
async def empleado_id(request):
    empleado_id = int(request.match_info['id'])
    empleado = next((e for e in leer_empleados() if e['id'] == empleado_id), None)
    if empleado:
        return web.json_response(empleado)
    return web.json_response({'message': 'Empleado no encontrado'}, status=404)

# Crear un nuevo empleado

# Actualizar un empleado
async def tareas_dia(request):

    try:
        empleado_id = int(request.match_info['id'])
        dia = int(request.match_info['dia'])  # Convertir a entero el día

        dias_semana = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"]

        empleado = next((e for e in leer_empleados() if e['id'] == empleado_id), None)

        if empleado:
            # Verificar si el empleado tiene tareas asignadas correctamente
            if 'tareas_asignadas' in empleado and isinstance(empleado['tareas_asignadas'], list) and len(empleado['tareas_asignadas']) > 0:
                tareas_dia = empleado['tareas_asignadas'][0].get(dias_semana[dia], [])
                return web.json_response({'tareas': tareas_dia})

            return web.json_response({'message': 'No hay tareas asignadas'}, status=404)

        return web.json_response({'message': 'Empleado no encontrado'}, status=404)

    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)
