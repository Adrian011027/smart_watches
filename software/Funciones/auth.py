from aiohttp import web
from utils.files import leer_users
import json
import os

async def login(request):
    return web.FileResponse('./web/login/login.html')

async def login_post(request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")

    users = leer_users().get("users", [])
    user_found = next((u for u in users if u.get("username") == username), None)

    if not user_found:
        return web.json_response({"success": False, "detail": "Usuario incorrecto"}, status=401)
    if user_found.get("password") != password:
        return web.json_response({"success": False, "detail": "Contraseña incorrecta"}, status=401)

    user = {
        "username": user_found["username"],
        "role": user_found["role"],
        "empleado_id": user_found["empleado_id"]
    }
    response = web.json_response({"success": True, "message": "Login exitoso", **user})
    response.set_cookie("usuario", json.dumps(user))
    return response

async def logout(request):
    response = web.HTTPFound("/login")
    response.del_cookie("usuario")
    return response
