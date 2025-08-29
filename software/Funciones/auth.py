# Funciones/auth.py

from aiohttp import web
import json
import os

def load_users():
    base_path = os.path.dirname(os.path.abspath(__file__))
    user_path = os.path.join(base_path, 'users.json')
    with open(user_path, 'r') as file:
        users_data = json.load(file)
    return users_data.get("users", [])

async def login(request):
    return web.FileResponse('./web/login/login.html')

async def login_post(request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    users = load_users()
    user_found = next((u for u in users if u.get("username") == username), None)
    if not user_found:
        return web.json_response({"success": False, "detail": "Usuario incorrecto"}, status=401)

    if user_found.get("password") != password:
        return web.json_response({"success": False, "detail": "Contraseña incorrecta"}, status=401)
    
    user = {
        "username": user_found.get("username"),
        "role": user_found.get("role"),
        "empleado_id": user_found.get("empleado_id")  
    }
    
    response = web.json_response({
        "success": True,
        "message": "Login exitoso",
        "empleado_id": user["empleado_id"],
        "role": user["role"]
    })
    
    response.set_cookie("usuario", json.dumps(user))
    return response

async def logout(request):
    response = web.HTTPFound('/login')
    response.del_cookie("usuario")
    return response
