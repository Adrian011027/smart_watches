# utils/files.py
import os
import json
from pydantic import SecretStr

BASE_DIR = os.getcwd()
EMP_PATH = os.path.join(BASE_DIR, "empleados.json")
USERS_PATH = os.path.join(BASE_DIR, "Funciones", "users.json")

# ---------------------------
# Empleados
# ---------------------------
def leer_empleados():
    if os.path.exists(EMP_PATH):
        with open(EMP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_empleados(empleados):
    with open(EMP_PATH, "w", encoding="utf-8") as f:
        json.dump(empleados, f, indent=2, ensure_ascii=False)

# ---------------------------
# Users
# ---------------------------
def leer_users():
    if os.path.exists(USERS_PATH):
        with open(USERS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": []}

def guardar_users(users):
    """
    Guarda la lista completa de usuarios en users.json
    """
    # Convertir SecretStr → str si existe
    for user in users:
        if isinstance(user.get("password"), SecretStr):
            user["password"] = user["password"].get_secret_value()

    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump({"users": users}, f, indent=2, ensure_ascii=False)

def guardar_user(user_data):
    """
    Agrega un único usuario a la lista
    """
    users = leer_users()
    users["users"].append(user_data)
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
