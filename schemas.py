from pydantic import BaseModel, Field
from datetime import time, date
from typing import Optional

class ActividadPost(BaseModel):
    nombre: str
    descripcion: str
    costo: float

class ActividadUpdate(BaseModel):
    nombre: str = None
    descripcion: str = None
    costo: float = None

class TurnoPost(BaseModel):
    hora_inicio: str
    hora_fin: str


class AlumnoPost(BaseModel):
    ci_alumno: int
    nombre: str
    apellido: str
    fecha_nacimiento: date 
    telefono: str = None
    correo: str = None
    contraseña: str = None