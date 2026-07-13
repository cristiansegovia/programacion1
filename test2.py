import secrets
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import json

app = FastAPI()
security = HTTPBearer()

# Base de datos simulada en memoria
# En producción, esto iría en Redis o una Base de Datos (SQL/NoSQL)
TOKEN_STORE = {
    "82f35e02563dae974fccbc1e7676c6c2b698f22f914ac218653d2af62c1c795c" : "usuario1"
}

# Simulación de usuarios registrados
USER_DATABASE = {
    "usuario1": "pass123"
}

class LoginRequest(BaseModel):
    username: str
    password: str

# 1. Endpoint para generar el token
@app.post("/login")
def login(data: LoginRequest):
    # Validación simple de credenciales
    user_password = USER_DATABASE.get(data.username)
    if not user_password or user_password != data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    # Generamos un token seguro y aleatorio (no es un JWT, es un string opaco)
    token = secrets.token_hex(32)

    # Guardamos el token asociado al usuario
    TOKEN_STORE[token] = data.username

    return {"access_token": token, "token_type": "bearer"}

# 2. Función de dependencia para validar el token
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    username = TOKEN_STORE.get(token)

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado!!!",
        )
    return username

# 3. Endpoint protegido
@app.get("/ruta-protegida")
def read_protected_data(username: str = Depends(get_current_user)):
    return {"mensaje": f"Hola {username}, tienes acceso a estos datos secretos."}

# 4. Obtener servidores con estado Activo
@app.get("/servidores-activos")
def obtener_servidores_activos():
    try:
        with open('servidores.json', 'r') as file:
            servidores = json.load(file)
    except FileNotFoundError:
        return {"mensaje": "No hay servidores registrados."}

    servidores_activos = [
        servidor
        for servidor in servidores.values()
        if isinstance(servidor, dict) and servidor.get("estado", "").lower() == "activo"
    ]

    return {"servidores_activos": servidores_activos}

# 5. Alta de servidores protegida por token, usando parámetros de consulta
@app.post("/servidores", status_code=status.HTTP_201_CREATED)
def crear_servidor(
    ip: str = Query(..., min_length=7),
    nombre: str = Query(..., min_length=1),
    estado: str = Query(..., min_length=1),
    username: str = Depends(get_current_user),
):
    try:
        with open('servidores.json', 'r') as file:
            servidores = json.load(file)
    except FileNotFoundError:
        return {"mensaje": "Archivo de servidores no encontrado. Se creará uno nuevo."}

    servidor_id = 1
    while str(servidor_id) in servidores:
        servidor_id += 1

    servidor = {
        "ip": ip,
        "nombre": nombre,
        "estado": estado,
    }
    with open('servidores.json', 'w') as file:
        servidores[str(servidor_id)] = servidor
        json.dump(servidores, file, indent=4)

    return {"mensaje": "Servidor registrado correctamente", "servidores": servidores}
