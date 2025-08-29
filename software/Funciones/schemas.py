from pydantic import BaseModel, Field, SecretStr
from typing import List, Optional, Dict, Literal

#Esquema para el json "users"
class Users(BaseModel):
    username: str = Field(None, min_length=4, max_length=20)
    password: SecretStr = Field(..., min_length=6, max_length=20)
    role: Literal["empleado", "administrador"]
    empleado_id: int = Field(None, gt=0, lt=100)
    
# Esquema para actualizar "users"
class UsersUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=4, max_length=20)
    role: Optional[Literal["empleado", "administrador"]]
    password: Optional[SecretStr] = Field(None, min_length=6, max_length=20) 
    
# Esquema para las tareas dentro de los días; las tareas son opcionales en el caso de create se crean vacias update las asigna
class TareaSchema(BaseModel):
    id: Optional[int] = Field(None, gt=0, lt=100)
    newId: Optional[int] = Field(None, gt=0, lt=100)
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = None
    hora: Optional[str] = None  # str es hora de inicio ejemplo: "09:30" / "14:30"
    estatus: Optional[int] = None  # 1-In Progress, 2-To Do, 3-Extras, 4-ExtraTerminada 0-Done

# Días de la semana en minúsculas
DIAS_SEMANA = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]

# Esquema para los empleados
class EmpleadoSchema(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    puesto: str = Field(..., min_length=2, max_length=100)
    tareas_asignadas: Dict[str, List[TareaSchema]] = Field(
        default_factory=lambda: {dia: [] for dia in DIAS_SEMANA}  # Inicializa con diccionarios vacíos
    )
    id: Optional[int] = None
    imagen: Optional[str] = None

# Esquema para actualizar empleados
class EmpleadoUpdateSchema(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    puesto: Optional[str] = Field(None, min_length=2, max_length=100)
    imagen: Optional[str] = Field(None, min_length=2, max_length=100)
    tareas_asignadas: Optional[Dict[str, List[TareaSchema]]] = None  # Mantiene la nueva estructura
