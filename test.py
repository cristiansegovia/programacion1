import secrets
from typing import Dict
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

app = FastAPI()
security = HTTPBearer()

# Base de datos simulada en memoria
# En producción, esto iría en Redis o una Base de Datos (SQL/NoSQL)
TOKEN_STORE = {}

# Simulación de usuarios registrados
USER_DATABASE = {
    "usuario1": "pass123"
}

# Base de datos simulada para libros
BOOKS_DB: Dict[int, dict] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


class Libro(BaseModel):
    id: int = Field(gt=0, description="Identificador único del libro")
    titulo: str = Field(min_length=1, description="Título del libro")
    autor: str = Field(min_length=1, description="Autor del libro")
    año: int = Field(gt=0, description="Año de publicación")


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


# 4. CRUD de libros protegido con Bearer token
@app.get("/libros")
def listar_libros(username: str = Depends(get_current_user)):
    return {"libros": list(BOOKS_DB.values())}


@app.get("/libros/{libro_id}")
def obtener_libro(libro_id: int, username: str = Depends(get_current_user)):
    libro = BOOKS_DB.get(libro_id)
    if not libro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libro no encontrado",
        )
    return libro


@app.post("/libros", status_code=status.HTTP_201_CREATED)
def crear_libro(libro: Libro, username: str = Depends(get_current_user)):
    if libro.id in BOOKS_DB:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El libro ya existe",
        )

    libro_data = libro.model_dump() if hasattr(libro, "model_dump") else libro.dict()
    BOOKS_DB[libro.id] = libro_data
    return {"mensaje": "Libro creado correctamente", "libro": BOOKS_DB[libro.id]}


@app.put("/libros/{libro_id}")
def actualizar_libro(libro_id: int, libro: Libro, username: str = Depends(get_current_user)):
    if libro_id != libro.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El id del path no coincide con el del cuerpo",
        )

    if libro_id not in BOOKS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libro no encontrado",
        )

    libro_data = libro.model_dump() if hasattr(libro, "model_dump") else libro.dict()
    BOOKS_DB[libro_id] = libro_data
    return {"mensaje": "Libro actualizado correctamente", "libro": BOOKS_DB[libro_id]}


@app.delete("/libros/{libro_id}")
def eliminar_libro(libro_id: int, username: str = Depends(get_current_user)):
    libro = BOOKS_DB.pop(libro_id, None)
    if libro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libro no encontrado: Error 404",
        )

    return {"mensaje": "Libro eliminado correctamente", "libro": libro}
