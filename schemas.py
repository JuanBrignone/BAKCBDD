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