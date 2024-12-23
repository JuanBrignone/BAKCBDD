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

class AlumnoResponse(BaseModel):
    ci_alumno: int
    nombre: str
    apellido: str
    fecha_nacimiento: date
    telefono: str
    correo: str
    contraseña: str

    
class ClaseResponse(BaseModel):
    id_clase: int
    id_actividad: int   
    nombre_actividad: str
    nombre_instructor: str 
    hora_inicio: time
    hora_fin: time
    costo_actividad: int

class AlumnoClaseRequest(BaseModel):
    id_clase: int
    ci_alumno: int
    id_equipamiento: int = None

class LoginRequest(BaseModel):
    correo: str
    contraseña: str

class LoginResponse(BaseModel):
    message: str

class AlumnoUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None
    contraseña: Optional[str] = None

class ActividadCantidad(BaseModel):
    actividad: str
    cantidad_alumnos: int


class ClasePost(BaseModel):
    ci_instructor: int
    nombre_actividad: str  
    id_turno: int
    dictada: bool

class InstructorPost(BaseModel):
    ci_instructor: int
    nombre: str
    apellido: str