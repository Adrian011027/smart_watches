from aiohttp import web
from utils.files import leer_users, leer_empleados
import json, bcrypt

async def login(request):
    return web.FileResponse('./web/login/login.html')

async def login_post(request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return web.json_response({"success": False, "detail": "Faltan credenciales"}, status=400)

    # =========================
    # 1️⃣ Buscar en users.json
    # =========================
    users = leer_users().get("users", [])
    user_found = next((u for u in users if u.get("username") == username), None)

    if user_found:
        hashed = user_found.get("password")
        # Comparar con bcrypt si está en hash
        if hashed and bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8")):
            role = user_found.get("role", "empleado")
            empleado_id = user_found.get("empleado_id")
            user = {
                "username": username,
                "role": role,
                "empleado_id": empleado_id,
                "tipo": "user"
            }
            response = web.json_response({"success": True, "message": "Login exitoso", **user})
            response.set_cookie("usuario", json.dumps(user))
            return response
        else:
            return web.json_response({"success": False, "detail": "Contraseña incorrecta"}, status=401)

    # =============================
    # 2️⃣ Buscar en empleados.json
    # =============================
    empleados = leer_empleados()
    empleado_found = next((e for e in empleados if e.get("username") == username), None)

    if empleado_found:
        hashed = empleado_found.get("password_dp")
        if hashed:
            # Si estaba en texto plano, comparar directo
            if hashed == password or bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8")):
                role = empleado_found.get("role_dp", "empleado")
                empleado_id = empleado_found.get("id")
                user = {
                    "username": username,
                    "role": role,
                    "empleado_id": empleado_id,
                    "tipo": "empleado"
                }
                response = web.json_response({"success": True, "message": "Login exitoso", **user})
                response.set_cookie("usuario", json.dumps(user))
                return response
        return web.json_response({"success": False, "detail": "Contraseña incorrecta"}, status=401)

    # =============================
    # ❌ Ninguno encontrado
    # =============================
    return web.json_response({"success": False, "detail": "Usuario no encontrado"}, status=404)


async def logout(request):
    response = web.HTTPFound("/login")
    response.del_cookie("usuario")
    return response
