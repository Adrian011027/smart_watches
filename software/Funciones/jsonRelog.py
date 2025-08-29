
import os
import json
import requests
from datetime import datetime

#1-El reloj manda el id de la tarea en cuestion 
#   Hay 2 posibles cambios :
#       -la tarea excedio su  tiempo limite | estatus = 3
#       -la tarea se compelto en tiempo y forma | estatus = 0
#2-Se modifica el json de empleados 
#3-Una vez modifciado este se envia a los relojes

def leer_empleados():
    archivo_empleados = './empleados.json'
    if os.path.exists(archivo_empleados):
        with open(archivo_empleados, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

#variables hardcodeadas en lo que el relog mande respectivos datos
id_empleado=10
id_task_complete = 1

dias = {
    'Monday': 'lunes',
    'Tuesday': 'martes',
    'Wednesday': 'miércoles',
    'Thursday': 'jueves',
    'Friday': 'viernes',
    'Saturday': 'sábado',
    'Sunday': 'domingo'
}

empleados = leer_empleados()


#lista de tareas extras
def tareas_asignadas_persona(empleado_id):
    """Devuelve una lista de tareas del empleado seleccionado."""
    empleados = leer_empleados()
    empleado = next((e for e in empleados if e["id"] == empleado_id), None)

    if not empleado:
        return []  # o lanza una excepción si prefieres

    dia_actual = dias[datetime.today().strftime('%A')]
    return empleado["tareas_asignadas"].get(dia_actual, [])

def filtrar_tareas_con_estatus(empleados, estatus=3):
    """Devuelve una lista de tareas con un estatus específico de todos los empleados."""
    tareas_filtradas = []
    diaActual = dias[datetime.today().strftime('%A')]
    for empleado in empleados:
        for dia, tareas in empleado.get("tareas_asignadas", {}).items():
            for tarea in tareas:
                if tarea.get("estatus") == estatus and dia == diaActual:
                    tareas_filtradas.append({
                        "id_empleado": empleado.get("id"),
                        "nombre": empleado.get("nombre"),
                        "dia": dia,
                        "tarea": tarea
                    })
    print("tareas_filtradas")
    return tareas_filtradas

def tareas_completada(id_empleado,id_task_complete):
    
    dia = dias[datetime.today().strftime('%A')]
    print(dia)
    data = {
        "id" : id_task_complete,
        "estatus" :  0
    }
    newdata = {
    "tareas_asignadas": {
        dia: [data]
    }
    }
    print(newdata)
    response = requests.patch(f"http://localhost:2298/empleados/{id_empleado}/estatus",
                          json=newdata,
                          headers={"Content-Type": "application/json"})
    
    print("Status:", response.status_code)
    print("Respuesta:", response.json())
    return #retorno respons pero con json
##tareas_completada(10, 1)
# Leer el JSON de empleados
empleados = leer_empleados()

# Filtrar empleados con tareas de estatus = 3
resultado = filtrar_tareas_con_estatus(empleados, estatus=3)
#print(resultado)

resi= tareas_asignadas_persona(empleado_id=2)
print(resi)
# Mostrar el resultado filtrado
#print(json.dumps(resultado, indent=4, ensure_ascii=False))
