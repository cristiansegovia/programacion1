import secrets
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.params import Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

app = FastAPI()
security = HTTPBearer()

# Base de datos simulada en memoria
# En producción, esto iría en Redis o una Base de Datos (SQL/NoSQL)
TOKEN_STORE = {
    "cristian" : "82f35e02563dae974fccbc1e7676c6c2b698f22f914ac218653d2af62c1c795c"
}

# Simulación de usuarios registrados
USER_DATABASE = {
    "usuario1": "pass123",
    "cristian": "asdqwe123"
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
            detail="Token inválido o expirado",
        )
    return username

# 3. Endpoint protegido
@app.get("/ruta-protegida")
def read_protected_data(username: str = Depends(get_current_user)):
    return {"mensaje": f"Hola {username}, tienes acceso a estos datos secretos."}

names=[]

@app.post("/nombres/{nombre}")
def recibir_nombre(username: str = Depends(get_current_user), nombre: str = None):
    names.append(nombre)
    return {"mensaje": "El nombre se guardo correctamente", "nombres": names}


class Servidor(BaseModel):
    nombre: str
    id: str
    estado: str

servidores : []

@app.post("/servidores")
def recibir_servidor(username: str = Depends(get_current_user), servidor: Servidor = None):
    servidores : []
    servidores.append(servidor)
    return {"mensaje": "El servidor se guardo correctamente", "servidores": servidores}
